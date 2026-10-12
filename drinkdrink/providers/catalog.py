"""Small, explicit boundary around documented official ordering surfaces.

The caller supplies an authenticated MCP transport. This module never reads tokens,
installs vendor software, or guesses prices from an upstream response.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse


CATALOG_DIR = Path(__file__).with_name("manifests")
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
READ_ONLY_ACTIONS = frozenset({
    "discover_stores", "delivery_stores", "search_drinks", "product_detail",
    "preview_order", "get_order", "store_coupons", "my_coupons",
})


class CatalogError(ValueError):
    pass


class AuthorizationError(PermissionError):
    pass


def argument_digest(arguments: Mapping[str, Any]) -> str:
    """Fingerprint the exact JSON arguments authorized for one mutation."""
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MutationAuthorization:
    action: str
    arguments_sha256: str
    instruction: str


@dataclass(frozen=True)
class ProviderModule:
    id: str
    brand: str
    surface: str
    audience: str
    status: str
    verified_on: date
    source_urls: tuple[str, ...]
    endpoint: str | None
    capabilities: Mapping[str, str]
    notes: str

    @classmethod
    def from_file(cls, path: Path) -> "ProviderModule":
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {"id", "brand", "surface", "audience", "status", "verified_on", "source_urls", "endpoint", "capabilities", "notes"}
        if set(data) != required:
            raise CatalogError(f"{path.name}: fields differ from catalog schema")
        if not ID_PATTERN.fullmatch(data["id"]) or path.stem != data["id"]:
            raise CatalogError(f"{path.name}: invalid module id")
        if data["surface"] not in {"mcp", "cli", "skill", "developer_portal"}:
            raise CatalogError(f"{path.name}: unknown surface")
        if data["audience"] not in {"consumer", "merchant_or_partner"}:
            raise CatalogError(f"{path.name}: unknown audience")
        if data["status"] not in {"documented", "research_only"}:
            raise CatalogError(f"{path.name}: unknown status")
        if not isinstance(data["source_urls"], list) or not data["source_urls"]:
            raise CatalogError(f"{path.name}: missing official sources")
        urls = [*data["source_urls"], *([data["endpoint"]] if data["endpoint"] else [])]
        if any(urlparse(url).scheme != "https" or not urlparse(url).netloc for url in urls):
            raise CatalogError(f"{path.name}: sources and endpoint must be HTTPS URLs")
        capabilities = data["capabilities"]
        if not isinstance(capabilities, dict) or any(
            not ID_PATTERN.fullmatch(k) or not isinstance(v, str) or not v
            for k, v in capabilities.items()
        ):
            raise CatalogError(f"{path.name}: invalid capability map")
        if data["surface"] != "mcp" and capabilities:
            raise CatalogError(f"{path.name}: only MCP tools are callable here")
        if data["status"] == "documented" and data["surface"] == "mcp" and not data["endpoint"]:
            raise CatalogError(f"{path.name}: documented MCP needs an endpoint")
        return cls(
            id=data["id"], brand=data["brand"], surface=data["surface"],
            audience=data["audience"], status=data["status"],
            verified_on=date.fromisoformat(data["verified_on"]),
            source_urls=tuple(data["source_urls"]), endpoint=data["endpoint"],
            capabilities=capabilities, notes=data["notes"],
        )

    def supports(self, action: str, available_tools: set[str] | None = None) -> bool:
        """Metadata support; pass host tool names to check live availability too."""
        tool = self.capabilities.get(action)
        return bool(
            self.surface == "mcp" and self.audience == "consumer"
            and self.status == "documented" and tool
            and (available_tools is None or tool in available_tools)
        )

    def call(
        self,
        action: str,
        arguments: Mapping[str, Any],
        invoke_tool: Callable[[str, str, Mapping[str, Any]], Any],
        *,
        available_tools: set[str] | None = None,
        authorization: MutationAuthorization | None = None,
    ) -> Any:
        """Call an already connected host transport; return its unmodified result."""
        if not self.supports(action, available_tools):
            raise CatalogError(f"{self.id}: action {action!r} is unavailable")
        # New actions require explicit authorization until classified as read-only.
        if action not in READ_ONLY_ACTIONS and (
            authorization is None
            or authorization.action != action
            or authorization.arguments_sha256 != argument_digest(arguments)
            or not authorization.instruction.strip()
        ):
            raise AuthorizationError("mutation needs an explicit instruction for these exact arguments")
        return invoke_tool(self.endpoint, self.capabilities[action], arguments)


def load_catalog(directory: Path = CATALOG_DIR) -> dict[str, ProviderModule]:
    modules = [ProviderModule.from_file(path) for path in sorted(directory.glob("*.json"))]
    if len({module.id for module in modules}) != len(modules):
        raise CatalogError("duplicate module id")
    return {module.id: module for module in modules}
