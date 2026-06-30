class PluginBase:

    @staticmethod
    def about(title="", summary=""):
        return {
            "title": title,
            "summary": summary,
        }

    @staticmethod
    def status_ok(title, message):
        return {
            "state": "ok",
            "title": title,
            "message": message,
        }

    @staticmethod
    def status_warning(title, message):
        return {
            "state": "warning",
            "title": title,
            "message": message,
        }

    @staticmethod
    def status_error(title, message):
        return {
            "state": "error",
            "title": title,
            "message": message,
        }
