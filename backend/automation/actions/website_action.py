import webbrowser


class WebsiteAction:

    def execute(self, step, apps):

        url = step.get("url") or ""

        if "://" not in url:
            url = "https://" + url

        print(f"🌐 Opening {url}")

        if not webbrowser.open(url):
            raise RuntimeError(f"Could not open {url}")
