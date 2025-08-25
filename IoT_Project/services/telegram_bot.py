# telegram_bot.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
import requests, json
import logging

from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.telBot_graph_table_generator import generate_graph_image, generate_table_image


# ---------------- States ----------------
DATA_MENU, GRAPHS_TYPE, GRAPHS_SENSOR, TABLES_TYPE, TABLES_SENSOR = range(5)
BUILDING, LATITUDE, LONGITUDE, CHOOSE_BUILDING, CHOOSE_DEVICE = range(5, 10)
# Renaming for clarity and consistency
ADD_DEVICE_CHOOSE_BUILDING, ADD_DEVICE_CHOOSE_TYPE = range(10, 12)
REMOVE_DEVICE_TYPE, REMOVE_DEVICE_BUILDING, REMOVE_DEVICE_ID = range(12, 15)
GRAPHS_SENSOR_ID, TABLES_SENSOR_ID = range(15, 17)
DEFINE_LOCATION_BUILDING, DEFINE_LOCATION_LAT, DEFINE_LOCATION_LON = range(17, 20)

def escape_markdown_v2(text: str) -> str:
    """Escapes special characters for MarkdownV2."""
    special_chars = '_*[]()~>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in special_chars else c for c in text)

# ---------------- Helper Function ----------------
def fetch_json(url, params=None, method="get", payload=None, timeout=10):
    """
    Fetches JSON data from a URL with error handling.
    """
    try:
        if method == "get":
            r = requests.get(url, params=params, timeout=timeout)
        else:
            r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

class QuakeBot:
    def __init__(self):
        self.buildings = {}
        self.device_types = ["Accelerometer_Sensor", "Velocity_Sensor", "Buzzer",
                            "FlashingLight", "ElectricityCutoff", "GasCutoff",
                            "WaterCutoff"]
        self.sensor_types = ["Accelerometer_Sensor", "Velocity_Sensor"]
        
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        cfg = ConfigLoader()
        self.token = cfg.Token_config
        self.service_url = cfg.static_web_url
        self.catalog_url = cfg.catalog_url

        # Register bot in catalog
        registrar = DeviceRegistrar(self.catalog_url)
        registrar.register({
            "type": "Telegram_Bot",
            "building": "Central_Unit",
            "location": {"latitude": "Central_Unit", "longitude": "Central_Unit"}
        })

    # ---------------- Start / Menu ----------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            ["🏘 Define project locations"],
            ["➕ Add Devices", "➖ Remove Devices"],
            ["📡 Devices", "📊 System Status"],
            ["📈 Data", "❓ Help"],
            ["🔄 Reactivate System", "⛔ Shut Off System"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Choose an option please:", reply_markup=reply_markup)
        return ConversationHandler.END

    async def return_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔙 Returning to main menu...", reply_markup=ReplyKeyboardRemove())
        await self.start(update, context)
        return ConversationHandler.END

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "❓ Help\n"
            "You are setting up and monitoring an IoT project.\n"
            "🏘 Define project locations — install places\n"
            "➕ Add Devices — add a device\n"
            "➖ Remove Devices — remove a device\n"
            "📡 Devices — list all defined sensors & actuators\n"
            "📊 System Status — system performance status\n"
            "📈 Data — view acceleration/velocity charts and tables\n"
            "🔄 Reactivate — manual reactivation after event\n"
            "⛔ Shut Off — manually shut off utilities"
        )
    
    # ---------------- Other Functions ----------------
    async def system_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status_data = fetch_json(f"{self.service_url}/status")
        if "error" in status_data:
            await update.message.reply_text(f"⚠️ Error fetching status: {status_data['error']}")
            return

        state = status_data.get("system_status", "UNKNOWN")
        await update.message.reply_text(f"📊 System Status: {state}")
            
    async def reactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        resp = requests.post(f"{self.service_url}/reactivate", json={}, timeout=10)
        if "error" in resp:
            await update.message.reply_text(f"⚠️ Error: {resp['error']}")
        else:
            await update.message.reply_text("🔄 Reactivate sent.")

    async def shutoff(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            r = requests.post(f"{self.service_url}/manual_shutoff", json={}, timeout=10)
            r.raise_for_status()
            await update.message.reply_text("⛔ Shut-off sent.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def show_devices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sensors = fetch_json(f"{self.service_url}/sensors")
        actuators = fetch_json(f"{self.service_url}/actuators")

        if "error" in sensors or "error" in actuators:
            await update.message.reply_text(f"⚠️ Error fetching devices: {sensors.get('error') or actuators.get('error')}")
            return

        lines = []
        if sensors:
            lines.append("📡 Sensors:")
            for device_id, info in sensors.items():
                loc = info.get("location", {})
                lines.append(f"{device_id} | {info.get('type')} | {info.get('building')} | ({loc.get('latitude','?')},{loc.get('longitude','?')})")
        else:
            lines.append("⚠️ No sensors yet!")

        if actuators:
            lines.append("\n🔧 Actuators:")
            for device_id, info in actuators.items():
                loc = info.get("location", {})
                lines.append(f"{device_id} | {info.get('type')} | {info.get('building')} | ({loc.get('latitude','?')},{loc.get('longitude','?')})")
        else:
            lines.append("\n⚠️ No actuators yet!")

        await update.message.reply_text("\n".join(lines))

    # ---------------- Data Menu (Graphs & Tables) ----------------
    async def show_data_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            ["📈 Graphs", "📋 Tables"],
            ["🔙 Return to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Please choose a data view:", reply_markup=reply_markup)
        return DATA_MENU
    
    async def get_sensors_with_data(self):
        response = fetch_json(f"{self.service_url}/get_sensors_with_data")
        if "error" in response:
            self.logger.error(f"Error fetching sensors with data: {response['error']}")
            return []
        return response
        
    async def show_graphs_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sensors_with_data = await self.get_sensors_with_data()
        
        if not sensors_with_data:
            await update.message.reply_text("⚠️ No sensors with data found. Please check sensor activity.")
            await self.start(update, context)
            return ConversationHandler.END
            
        keyboard = [[s] for s in sensors_with_data]
        keyboard.append([KeyboardButton("🔙 Return to Main Menu")])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📈 Select a sensor to view its graph:", reply_markup=reply_markup)
        return GRAPHS_SENSOR_ID

    async def show_tables_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sensors_with_data = await self.get_sensors_with_data()
        
        if not sensors_with_data:
            await update.message.reply_text("⚠️ No sensors with data found. Please check sensor activity.")
            await self.start(update, context)
            return ConversationHandler.END

        keyboard = [[s] for s in sensors_with_data]
        keyboard.append([KeyboardButton("🔙 Return to Main Menu")])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📋 Select a sensor to view its table:", reply_markup=reply_markup)
        return TABLES_SENSOR_ID
    
    async def show_graph(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        device_id = update.message.text
        
        chart_data = fetch_json(f"{self.service_url}/get_chart_data", params={"sensor_id": device_id})
        
        if "error" in chart_data:
            await update.message.reply_text(f"❌ Error fetching data: {chart_data['error']}", reply_markup=ReplyKeyboardRemove(), parse_mode='MarkdownV2')
            await self.start(update, context)
            return ConversationHandler.END

        img_buffer = generate_graph_image(chart_data, device_id)
        escaped_device_id = escape_markdown_v2(device_id)
        await update.message.reply_photo(photo=img_buffer, caption=f"📊 Graph for sensor {escaped_device_id}", parse_mode='MarkdownV2')
        
        await self.start(update, context)
        return ConversationHandler.END
        
    async def show_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        device_id = update.message.text
        table_data = fetch_json(f"{self.service_url}/get_table_data", params={"sensor_id": device_id})

        if "error" in table_data:
            await update.message.reply_text(f"❌ Error fetching data: {table_data['error']}", reply_markup=ReplyKeyboardRemove(), parse_mode="MarkdownV2")
            await self.start(update, context)
            return ConversationHandler.END
        
        header = table_data['table_data']['header']
        rows = table_data['table_data']['rows']
        img_buffer = generate_table_image(header, rows)

        escaped_device_id = escape_markdown_v2(device_id)
        await update.message.reply_photo(
            photo=img_buffer,
            caption=f"📋 Table Data for sensor {escaped_device_id}",
            parse_mode="MarkdownV2"
        )
        await self.start(update, context)
        return ConversationHandler.END

    # ---------------- Conversation Handlers ----------------
    def data_conversation_handler(self):
        return ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^📈 Data$"), self.show_data_menu)],
            states={
                DATA_MENU: [
                    MessageHandler(filters.Regex(r"^📈 Graphs$"), self.show_graphs_type),
                    MessageHandler(filters.Regex(r"^📋 Tables$"), self.show_tables_type),
                    MessageHandler(filters.Regex(r"^🔙 Return to Main Menu$"), self.return_to_main_menu)
                ],
                GRAPHS_SENSOR_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔙 Return to Main Menu$"), self.show_graph),
                ],
                TABLES_SENSOR_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔙 Return to Main Menu$"), self.show_table),
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex(r"^🔙 Return to Main Menu$"), self.return_to_main_menu),
                CommandHandler("cancel", self.return_to_main_menu)
            ],
            allow_reentry=True
        )

    def define_location_handler(self):
        return ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^🏘 Define project locations$"), self.define_location_start)],
            states={
                DEFINE_LOCATION_BUILDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.define_location_building)],
                DEFINE_LOCATION_LAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.define_location_lat)],
                DEFINE_LOCATION_LON: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.define_location_lon)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_define_location)],
            allow_reentry=True
        )
        
    async def define_location_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏢 Please enter the building name (e.g., building_A):", parse_mode=None)
        return DEFINE_LOCATION_BUILDING

    async def define_location_building(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["building_name"] = update.message.text.strip()
        await update.message.reply_text("🌍 Now enter the latitude:", parse_mode=None)
        return DEFINE_LOCATION_LAT

    async def define_location_lat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            latitude = float(update.message.text.strip())
            context.user_data["latitude"] = latitude
            await update.message.reply_text("🌍 Now enter the longitude:", parse_mode=None)
            return DEFINE_LOCATION_LON
        except ValueError:
            await update.message.reply_text("⚠️ Invalid input. Please enter a valid number for latitude (e.g., 43.84 or 23):", parse_mode=None)
            return DEFINE_LOCATION_LAT

    async def define_location_lon(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            longitude = float(update.message.text.strip())
            building_name = context.user_data["building_name"]
            self.buildings[building_name] = {
                "location": {
                    "latitude": context.user_data["latitude"],
                    "longitude": longitude
                }
            }
            await update.message.reply_text(f"✅ Building '{building_name}' saved.", reply_markup=ReplyKeyboardRemove())
            await self.start(update, context)
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("⚠️ Invalid input. Please enter a valid number for longitude (e.g., 7.84 or 7):", parse_mode=None)
            return DEFINE_LOCATION_LON

    async def cancel_define_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Location definition cancelled.", reply_markup=ReplyKeyboardRemove())
        await self.start(update, context)
        return ConversationHandler.END

    def add_device_handler(self):
        return ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^➕ Add Devices$"), self.add_device_start)],
            states={
                ADD_DEVICE_CHOOSE_BUILDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_device_choose_building)],
                ADD_DEVICE_CHOOSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_device_choose_type)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_add_device)],
            allow_reentry=True
        )

    async def add_device_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.buildings:
            await update.message.reply_text("⚠️ No buildings defined yet! Please define project locations first.")
            return ConversationHandler.END
        keyboard = [[name] for name in self.buildings.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🏢 Select a building to add device to:", reply_markup=reply_markup)
        return ADD_DEVICE_CHOOSE_BUILDING

    async def add_device_choose_building(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        building = update.message.text
        if building not in self.buildings:
            await update.message.reply_text("⚠️ Invalid building selected!", reply_markup=ReplyKeyboardRemove())
            await self.start(update, context)
            return ConversationHandler.END
        context.user_data["building"] = building
        keyboard = [[d] for d in self.device_types]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📡 Select device type:", reply_markup=reply_markup)
        return ADD_DEVICE_CHOOSE_TYPE

    async def add_device_choose_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        device_type = update.message.text
        building = context.user_data["building"]
        if device_type not in self.device_types:
            await update.message.reply_text("⚠️ Invalid device type!", reply_markup=ReplyKeyboardRemove())
            await self.start(update, context)
            return ConversationHandler.END
        payload = {
            "type": device_type,
            "building": building,
            "location": self.buildings[building]["location"]
        }
        resp = fetch_json(f"{self.service_url}/add_device", method="post", payload=payload)
        
        if "error" in resp:
            await update.message.reply_text(f"⚠️ Failed to add device. Error: {resp['error']}", reply_markup=ReplyKeyboardRemove())
        else:
            escaped_payload = escape_markdown_v2(json.dumps(payload, indent=2))
            await update.message.reply_text(f"✅ Device added:\n{escaped_payload}", reply_markup=ReplyKeyboardRemove(), parse_mode='MarkdownV2')
        
        await self.start(update, context)
        return ConversationHandler.END
    
    async def cancel_add_device(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Device addition cancelled.", reply_markup=ReplyKeyboardRemove())
        await self.start(update, context)
        return ConversationHandler.END
    
    # ---------------- Remove Device ----------------
    def remove_device_handler(self):
        return ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^➖ Remove Devices$"), self.remove_device_start)],
            states={
                REMOVE_DEVICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.remove_device_choose_type)],
                REMOVE_DEVICE_BUILDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.remove_device_choose_building)],
                REMOVE_DEVICE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.remove_device_confirm)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_remove_device)],
            allow_reentry=True
        )

    async def remove_device_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Starts the remove device conversation."""
        if not self.buildings:
            await update.message.reply_text("⚠️ No buildings defined yet! Please define project locations first.")
            return ConversationHandler.END

        keyboard = [[d] for d in self.device_types]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🗑 Select the device type to remove:", reply_markup=reply_markup)
        return REMOVE_DEVICE_TYPE

    async def remove_device_choose_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Asks the user to choose a building after selecting a device type."""
        device_type = update.message.text
        if device_type not in self.device_types:
            await update.message.reply_text("⚠️ Invalid device type!", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        context.user_data["remove_type"] = device_type

        keyboard = [[b] for b in self.buildings.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🏢 Select the building:", reply_markup=reply_markup)
        return REMOVE_DEVICE_BUILDING

    async def remove_device_choose_building(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fetches and displays devices from the selected building and device type."""
        building = update.message.text
        device_type = context.user_data["remove_type"]

        if building not in self.buildings:
            await update.message.reply_text("⚠️ Invalid building!", reply_markup=ReplyKeyboardRemove())
            await self.start(update, context)
            return ConversationHandler.END

        context.user_data["remove_building"] = building

        data = fetch_json(f"{self.service_url}/devices_building", params={"type": device_type, "building": building})
        
        if "error" in data:
            await update.message.reply_text(f"❌ Error fetching devices: {data['error']}", reply_markup=ReplyKeyboardRemove(), parse_mode='MarkdownV2')
            await self.start(update, context)
            return ConversationHandler.END

        device_ids = data.get("matching_devices", [])

        if not device_ids:
            await update.message.reply_text("ℹ️ No devices found for this type in the selected building.", reply_markup=ReplyKeyboardRemove())
            await self.start(update, context)
            return ConversationHandler.END

        keyboard = [[d] for d in device_ids]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🔧 Select the device ID to remove:", reply_markup=reply_markup)
        return REMOVE_DEVICE_ID

    async def remove_device_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirms and sends a request to delete the selected device."""
        device_id = update.message.text
        device_type = context.user_data["remove_type"]

        payload = {"type": device_type, "device_id": device_id}

        resp = fetch_json(f"{self.service_url}/delete_device", method="post", payload=payload)
        
        if "error" in resp:
            await update.message.reply_text(f"❌ Failed to remove device. Error: {resp['error']}", reply_markup=ReplyKeyboardRemove(), parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(f"✅ Device {device_id} removed successfully.", reply_markup=ReplyKeyboardRemove())

        await self.start(update, context)
        return ConversationHandler.END

    async def cancel_remove_device(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancels the remove device conversation."""
        await update.message.reply_text("❌ Device removal cancelled.", reply_markup=ReplyKeyboardRemove())
        await self.start(update, context)
        return ConversationHandler.END

    # ---------------- RUN ----------------
    def run(self):
        app = ApplicationBuilder().token(self.token).build()

        app.add_handler(self.define_location_handler())
        app.add_handler(self.add_device_handler())
        app.add_handler(self.remove_device_handler()) # Added the new handler
        app.add_handler(self.data_conversation_handler())
        
        # Main Menu Handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.Regex(r"^📡 Devices$"), self.show_devices))
        app.add_handler(MessageHandler(filters.Regex(r"^📊 System Status$"), self.system_status))
        app.add_handler(MessageHandler(filters.Regex(r"^🔄 Reactivate System$"), self.reactivate))
        app.add_handler(MessageHandler(filters.Regex(r"^⛔ Shut Off System$"), self.shutoff))
        app.add_handler(MessageHandler(filters.Regex(r"^❓ Help$"), self.help))

        self.logger.info("QuakeBot started...")
        app.run_polling()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    QuakeBot().run()