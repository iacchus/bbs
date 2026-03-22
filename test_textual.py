import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Label
from textual.containers import Vertical
from textual import events, on

class MyWidget(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Header", classes="header", id="h")
        yield Label("Content")

    @on(events.Click, ".header")
    def handle_header_click(self, event: events.Click):
        self.app.bell()

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield MyWidget()

async def test():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.click("#h")
        print("Success")

asyncio.run(test())
