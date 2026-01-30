import random
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger


# Green tips and eco-friendly suggestions
GREEN_TIPS = [
    "🌱 Try using a reusable water bottle instead of single-use plastic bottles. You can save over 150 plastic bottles per year!",
    "🚲 Consider biking or walking for short trips. It's great for the environment and your health!",
    "💡 Switch to LED bulbs - they use 75% less energy and last 25 times longer than incandescent bulbs.",
    "🛍️ Bring your own reusable bags when shopping to reduce plastic waste.",
    "🌿 Start composting food scraps to reduce landfill waste and create nutrient-rich soil for gardening.",
    "🚿 Take shorter showers - reducing your shower time by just 2 minutes can save up to 10 gallons of water.",
    "🌳 Plant a tree! A single tree can absorb up to 48 pounds of CO2 per year.",
    "♻️ Recycle properly - rinse containers, remove caps, and check local guidelines for what can be recycled.",
    "🔌 Unplug electronics when not in use. 'Phantom' energy can account for 10% of your electricity bill.",
    "🥗 Try having one meatless day per week. Reducing meat consumption can significantly lower your carbon footprint.",
    "📦 Choose products with minimal packaging or packaging made from recycled materials.",
    "🌡️ Adjust your thermostat by just 1-2 degrees - it can save up to 10% on heating and cooling costs.",
    "🚗 If you drive, maintain proper tire pressure to improve fuel efficiency by up to 3%.",
    "💧 Fix leaky faucets - a dripping faucet can waste over 3,000 gallons of water per year.",
    "🌻 Start a small garden, even on a balcony. Growing your own herbs and vegetables reduces food miles.",
]


class Agent:
    def __init__(self):
        self.messenger = Messenger()

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Green Agent: Provides eco-friendly tips and sustainability advice.

        Args:
            message: The incoming message
            updater: Report progress (update_status) and results (add_artifact)
        """
        input_text = get_message_text(message).lower()

        await updater.update_status(
            TaskState.working, new_agent_text_message("🌍 Thinking green...")
        )

        # Generate response based on user input
        response = self._generate_green_response(input_text)

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=response))],
            name="Green Advice",
        )

    def _generate_green_response(self, input_text: str) -> str:
        """Generate an eco-friendly response based on input."""
        # Check for specific topics and provide targeted advice
        if any(word in input_text for word in ["water", "shower", "faucet", "hydration"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["water", "shower", "faucet", "💧", "🚿"])]
        elif any(word in input_text for word in ["energy", "electric", "power", "light", "bulb"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["energy", "electric", "bulb", "unplug", "💡", "🔌"])]
        elif any(word in input_text for word in ["plastic", "recycle", "waste", "garbage", "trash"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["plastic", "recycle", "waste", "♻️", "🛍️"])]
        elif any(word in input_text for word in ["transport", "car", "drive", "commute", "travel"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["bike", "walk", "drive", "car", "🚲", "🚗"])]
        elif any(word in input_text for word in ["food", "eat", "diet", "meat", "vegetable"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["food", "meat", "garden", "compost", "🥗", "🌻", "🌿"])]
        elif any(word in input_text for word in ["plant", "tree", "garden", "nature"]):
            tips = [t for t in GREEN_TIPS if any(w in t.lower() for w in ["tree", "plant", "garden", "🌳", "🌻", "🌱"])]
        else:
            tips = GREEN_TIPS

        # Select a random tip from the filtered list
        selected_tip = random.choice(tips) if tips else random.choice(GREEN_TIPS)

        # Format the response
        response = f"""🌍 **Green Agent Says:**

{selected_tip}

---
*Every small action counts! Together we can make a difference for our planet.* 🌿"""

        return response
