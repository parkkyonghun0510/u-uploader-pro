from typing import Optional, Tuple, Dict, List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from collections import defaultdict
import json
import time
import platform
import os
from pathlib import Path
import logging

from .Constant import Constant

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def load_metadata(metadata_json_path: Optional[str] = None) -> defaultdict:
    if metadata_json_path is None:
        return defaultdict(str)
    with open(metadata_json_path, encoding='utf-8') as f:
        return defaultdict(str, json.load(f))


class YouTubeUploader:
    """YouTubeUploader class for uploading videos via Selenium with metadata JSON."""

    def __init__(self, video_path: Optional[str] = None, metadata_json_path: Optional[str] = None,
                 thumbnail_path: Optional[str] = None,
                 profile_path: Optional[str] = None):
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.metadata_dict = load_metadata(metadata_json_path)
        self.browser = None
        self.profile_path = profile_path or str(Path.cwd() / "profile")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.is_mac = not any(os_name in platform.platform() for os_name in ["Windows", "Linux"])
        if self.video_path:
            self.__validate_inputs()

    def __validate_inputs(self):
        if not self.metadata_dict.get(Constant.VIDEO_TITLE):
            self.logger.warning("Title not found, defaulting to filename")
            self.metadata_dict[Constant.VIDEO_TITLE] = Path(self.video_path).stem

    def login(self) -> bool:
        """Launch interactive Firefox session to log in to YouTube and save cookies to the profile."""
        from selenium_firefox.firefox import Firefox
        os.makedirs(self.profile_path, exist_ok=True)
        self.logger.info(f"Opening browser for login with profile: {self.profile_path}")
        self.browser = Firefox(profile_path=self.profile_path, pickle_cookies=True, full_screen=False)
        try:
            self.browser.get(Constant.YOUTUBE_URL)
            time.sleep(Constant.USER_WAITING_TIME)
            if self.browser.has_cookies_for_current_website():
                self.browser.load_cookies()
                self.logger.info("Loaded existing cookies.")
                self.browser.refresh()
                time.sleep(Constant.USER_WAITING_TIME)

            print("\n" + "=" * 60)
            print("🔑 YOUTUBE INTERACTIVE LOGIN")
            print("1. In the opened Firefox window, sign in to your YouTube/Google account.")
            print("2. Ensure you reach YouTube / YouTube Studio with your channel active.")
            print("3. Return here and press [Enter] to save session cookies.")
            print("=" * 60 + "\n")
            try:
                input("Press [Enter] after completing sign-in in Firefox: ")
            except (EOFError, KeyboardInterrupt):
                pass

            self.browser.get(Constant.YOUTUBE_URL)
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.save_cookies()
            self.logger.info(f"✅ Session cookies successfully saved to {self.profile_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed during login session: {e}")
            raise
        finally:
            self.__quit()

    def upload(self) -> Tuple[bool, Optional[str]]:
        from selenium_firefox.firefox import Firefox
        os.makedirs(self.profile_path, exist_ok=True)
        self.browser = Firefox(profile_path=self.profile_path, pickle_cookies=True, full_screen=False)
        try:
            self.__login()
            return self.__upload_video()
        except Exception as e:
            print(f"Upload error: {e}")
            self.__quit()
            raise
        finally:
            self.__quit()

    def __login(self):
        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        if self.browser.has_cookies_for_current_website():
            self.browser.load_cookies()
            self.logger.debug("Loaded cookies")
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.refresh()
        else:
            self.logger.warning("No saved cookies found. Requesting sign-in...")
            print("Please sign in to YouTube in the browser window and press enter.")
            try:
                input("Press [Enter] once signed in: ")
            except (EOFError, KeyboardInterrupt):
                pass
            self.browser.get(Constant.YOUTUBE_URL)
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.save_cookies()

    def __clear_field(self, field):
        field.click()
        time.sleep(Constant.USER_WAITING_TIME)
        if self.is_mac:
            field.send_keys(Keys.COMMAND + 'a')
        else:
            field.send_keys(Keys.CONTROL + 'a')
        time.sleep(Constant.USER_WAITING_TIME)
        field.send_keys(Keys.BACKSPACE)

    def __write_in_field(self, field, string, select_all=False):
        if select_all:
            self.__clear_field(field)
        else:
            field.click()
            time.sleep(Constant.USER_WAITING_TIME)
        field.send_keys(string)

    def __upload_video(self) -> Tuple[bool, Optional[str]]:
        edit_mode = self.metadata_dict.get(Constant.VIDEO_EDIT)
        if edit_mode:
            self.browser.get(edit_mode)
            time.sleep(Constant.USER_WAITING_TIME)
        else:
            self.browser.get(Constant.YOUTUBE_URL)
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.get(Constant.YOUTUBE_UPLOAD_URL)
            time.sleep(Constant.USER_WAITING_TIME)
            absolute_video_path = str(Path.cwd() / self.video_path)
            self.browser.find(By.XPATH, Constant.INPUT_FILE_VIDEO).send_keys(absolute_video_path)
            self.logger.debug('Attached video')

            uploading_status_container = None
            while uploading_status_container is None:
                time.sleep(Constant.USER_WAITING_TIME)
                uploading_status_container = self.browser.find(By.XPATH, Constant.UPLOADING_STATUS_CONTAINER)

        if self.thumbnail_path is not None:
            absolute_thumbnail_path = str(Path.cwd() / self.thumbnail_path)
            self.browser.find(By.XPATH, Constant.INPUT_FILE_THUMBNAIL).send_keys(absolute_thumbnail_path)
            self.browser.driver.execute_script(
                "document.getElementById('file-loader').style = 'display: block! important'")

        title_field, description_field = self.browser.find_all(By.ID, Constant.TEXTBOX_ID, timeout=15)
        self.__write_in_field(title_field, self.metadata_dict[Constant.VIDEO_TITLE], select_all=True)

        video_description = self.metadata_dict[Constant.VIDEO_DESCRIPTION]
        video_description = video_description.replace("\n", Keys.ENTER)
        if video_description:
            self.__write_in_field(description_field, video_description, select_all=True)

        kids_section = self.browser.find(By.NAME, Constant.NOT_MADE_FOR_KIDS_LABEL)
        kids_section.location_once_scrolled_into_view
        time.sleep(Constant.USER_WAITING_TIME)
        self.browser.find(By.ID, Constant.RADIO_LABEL, kids_section).click()

        playlist = self.metadata_dict.get(Constant.VIDEO_PLAYLIST)
        if playlist:
            self.browser.find(By.CLASS_NAME, Constant.PL_DROPDOWN_CLASS).click()
            time.sleep(Constant.USER_WAITING_TIME)
            search_field = self.browser.find(By.ID, Constant.PL_SEARCH_INPUT_ID)
            self.__write_in_field(search_field, playlist)
            time.sleep(Constant.USER_WAITING_TIME * 2)
            playlist_items_container = self.browser.find(By.ID, Constant.PL_ITEMS_CONTAINER_ID)
            playlist_item = self.browser.find(By.XPATH, Constant.PL_ITEM_CONTAINER.format(playlist), playlist_items_container)
            if playlist_item:
                playlist_item.click()
                time.sleep(Constant.USER_WAITING_TIME)
            else:
                self.__clear_field(search_field)
                time.sleep(Constant.USER_WAITING_TIME)
                new_playlist_button = self.browser.find(By.CLASS_NAME, Constant.PL_NEW_BUTTON_CLASS)
                new_playlist_button.click()
                create_playlist_container = self.browser.find(By.ID, Constant.PL_CREATE_PLAYLIST_CONTAINER_ID)
                playlist_title_textbox = self.browser.find(By.XPATH, "//textarea", create_playlist_container)
                self.__write_in_field(playlist_title_textbox, playlist)
                time.sleep(Constant.USER_WAITING_TIME)
                create_playlist_button = self.browser.find(By.CLASS_NAME, Constant.PL_CREATE_BUTTON_CLASS)
                create_playlist_button.click()
                time.sleep(Constant.USER_WAITING_TIME)
            done_button = self.browser.find(By.CLASS_NAME, Constant.PL_DONE_BUTTON_CLASS)
            done_button.click()

        self.browser.find(By.ID, Constant.ADVANCED_BUTTON_ID).click()
        time.sleep(Constant.USER_WAITING_TIME)

        tags = self.metadata_dict.get(Constant.VIDEO_TAGS)
        if tags:
            tags_container = self.browser.find(By.ID, Constant.TAGS_CONTAINER_ID)
            tags_field = self.browser.find(By.ID, Constant.TAGS_INPUT, tags_container)
            self.__write_in_field(tags_field, ','.join(tags))

        self.browser.find(By.ID, Constant.NEXT_BUTTON).click()
        self.browser.find(By.ID, Constant.NEXT_BUTTON).click()
        self.browser.find(By.ID, Constant.NEXT_BUTTON).click()

        schedule = self.metadata_dict.get(Constant.VIDEO_SCHEDULE)
        if schedule:
            from datetime import datetime as dt
            upload_time_object = dt.strptime(schedule, "%m/%d/%Y, %H:%M")
            self.browser.find(By.ID, Constant.SCHEDULE_CONTAINER_ID).click()
            self.browser.find(By.ID, Constant.SCHEDULE_DATE_ID).click()
            self.browser.find(By.XPATH, Constant.SCHEDULE_DATE_TEXTBOX).clear()
            self.browser.find(By.XPATH, Constant.SCHEDULE_DATE_TEXTBOX).send_keys(upload_time_object.strftime("%b %e, %Y"))
            self.browser.find(By.XPATH, Constant.SCHEDULE_DATE_TEXTBOX).send_keys(Keys.ENTER)
            self.browser.find(By.XPATH, Constant.SCHEDULE_TIME).click()
            self.browser.find(By.XPATH, Constant.SCHEDULE_TIME).clear()
            self.browser.find(By.XPATH, Constant.SCHEDULE_TIME).send_keys(upload_time_object.strftime("%H:%M"))
            self.browser.find(By.XPATH, Constant.SCHEDULE_TIME).send_keys(Keys.ENTER)
        else:
            public_main_button = self.browser.find(By.NAME, Constant.PUBLIC_BUTTON)
            self.browser.find(By.ID, Constant.RADIO_LABEL, public_main_button).click()

        video_id = self.__get_video_id()

        uploading_status_container = self.browser.find(By.XPATH, Constant.UPLOADING_STATUS_CONTAINER)
        while uploading_status_container is not None:
            uploading_progress = uploading_status_container.get_attribute('value')
            self.logger.debug(f'Upload progress: {uploading_progress}%')
            time.sleep(Constant.USER_WAITING_TIME * 5)
            uploading_status_container = self.browser.find(By.XPATH, Constant.UPLOADING_STATUS_CONTAINER)

        done_button = self.browser.find(By.ID, Constant.DONE_BUTTON)
        if done_button.get_attribute('aria-disabled') == 'true':
            error_message = self.browser.find(By.XPATH, Constant.ERROR_CONTAINER).text
            self.logger.error(f"Upload error: {error_message}")
            return False, None

        done_button.click()
        time.sleep(Constant.USER_WAITING_TIME)
        self.browser.get(Constant.YOUTUBE_URL)
        self.__quit()
        return True, video_id

    def __get_video_id(self) -> Optional[str]:
        try:
            video_url_container = self.browser.find(By.XPATH, Constant.VIDEO_URL_CONTAINER)
            video_url_element = self.browser.find(By.XPATH, Constant.VIDEO_URL_ELEMENT, video_url_container)
            return video_url_element.get_attribute(Constant.HREF).split('/')[-1]
        except Exception:
            return None

    def add_log(self, message: str):
        self.logger.info(message)
        if hasattr(self, 'job_id') and self.job_id:
            pass  # Log would be stored in UploadJob if needed

    def __quit(self):
        try:
            if self.browser:
                self.browser.driver.quit()
        except Exception:
            pass
