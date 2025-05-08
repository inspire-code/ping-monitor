import sys

# ✅ Patch for PyInstaller's --noconsole mode
if sys.stdin is None:
    import io
    sys.stdin = io.StringIO()

import subprocess
import winsound
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURATION
critical_ips = {
    "1.1.1.1": "MIB SERVER",
    "8.8.8.8": "Google DNS"
}

critical_contact = "Mohd Ilham"
check_interval = 10  # seconds
chrome_profile_path = r"C:\PingMonitor\chrome_profile"

# Sound files
sound_alert_critical = "alert_critical.wav"
sound_alert_recovery = "alert_recovery.wav"
sound_alert_success = "alert_success.wav"
sound_alert_failure = "alert_failure.wav"

ip_status = {}

# FUNCTIONS

def play_sound(file):
    """Play a .wav sound file asynchronously if it exists."""
    try:
        winsound.PlaySound(file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except RuntimeError as e:
        print(f"🔇 Could not play sound {file}: {e}")

def setup_whatsapp():
    """ Launch Chrome and open WhatsApp Web with saved session. """
    print("Starting browser...")
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument(f"--user-data-dir={chrome_profile_path}")
    options.add_argument("--profile-directory=Default")
    
    driver = uc.Chrome(options=options)

    print("Opening WhatsApp Web...")
    driver.get("https://web.whatsapp.com/")

    try:
        print("Waiting for WhatsApp Web to be ready...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @role="textbox"]'))
        )
        print("✅ WhatsApp Web is ready!")
    except Exception as e:
        print(f"❌ Failed to load WhatsApp Web: {e}")
        driver.quit()
        exit()

    return driver

def ping(ip, timeout=2):
    """ Ping an IP address to check if it's reachable. """
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout * 1000), ip],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return False

def send_whatsapp_message(driver, contact, message, retries=3):
    """ Try to send a WhatsApp message. Retry if needed. """
    for attempt in range(1, retries + 1):
        try:
            search_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @role="textbox"]'))
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(contact)
            time.sleep(2)

            chat = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact}"]'))
            )
            chat.click()

            message_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @data-tab="10"]'))
            )
            message_box.click()
            message_box.send_keys(message + "\n")
            print(f"✅ Sent to {contact}: {message}")
            play_sound(sound_alert_success)
            return

        except Exception as e:
            print(f"❌ Attempt {attempt} failed to send message to {contact}: {e}")
            time.sleep(3)

    play_sound(sound_alert_failure)
    raise RuntimeError(f"All attempts to send message to {contact} failed.")

# MAIN EXECUTION

driver = setup_whatsapp()

while True:
    try:
        critical_down = []

        for ip, name in critical_ips.items():
            is_alive = ping(ip)
            if not is_alive:
                if ip_status.get(ip) != "down":
                    critical_down.append(f"{name} ({ip})")
                    ip_status[ip] = "down"
            else:
                if ip_status.get(ip) == "down":
                    send_whatsapp_message(driver, critical_contact, f"✅ Critical Recovery: {name} ({ip}) is back online.")
                    play_sound(sound_alert_recovery)
                    ip_status[ip] = "up"

        if critical_down:
            message = "[CRITICAL ALERT] ⚠️❗❌ The following are unreachable: " + ", ".join(critical_down) + " ❗❌⚠️"
            send_whatsapp_message(driver, critical_contact, message)
            play_sound(sound_alert_critical)

        time.sleep(check_interval)

    except RuntimeError as err:
        print(f"🔁 Reinitializing browser due to error: {err}")
        driver.quit()
        time.sleep(5)
        driver = setup_whatsapp()
