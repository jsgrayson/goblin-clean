from loguru import logger

class GmailArchiver:
    def archive(self):
        logger.info("Archiving Gmail...")
        return True

if __name__ == "__main__":
    g = GmailArchiver()
    g.archive()
