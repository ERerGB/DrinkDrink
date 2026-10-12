# Local lifecycle journal

Use the journal only if tracking across sessions helps the buyer. It stores an idea and observed events in a local `*.journal.json` file, which Git ignores. Do not put names, addresses, phone numbers, tokens, or full order screenshots in the note or evidence fields.

```sh
python3 drinkdrink/scripts/journal.py start --idea "a large iced latte"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event discovered --note "three channels found"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event quoted
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event selected --note "pickup path selected"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event submitted --evidence "order confirmation shown in app"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event payment_paid --evidence "payment success shown in app"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event accepted --evidence "merchant accepted in app"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event ready_for_pickup
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event received --evidence "buyer confirmed pickup"
python3 drinkdrink/scripts/journal.py record --id ORDER_ID --event completed
```

Stages are idea → discovered → quoted → selected → submitted → accepted → in transit / ready for pickup → received → completed. Payment events are independent because payment timing varies by channel. Cancellation, issue, and refund stages are supported. A stage change that asserts submission, acceptance, receipt, or refund needs evidence from the relevant app or buyer. The journal records events; it does not contact merchants or verify claims itself.
