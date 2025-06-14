import pandas as pd
import matplotlib.pyplot as plt

# Load your actual learning log
df = pd.read_csv("learning_log.csv")

# Plot reward over time
plt.figure(figsize=(10, 4))
plt.plot(df["episode"], df["reward"], marker="o")
plt.title("Reward over Learning Episodes")
plt.xlabel("Episode")
plt.ylabel("Reward")
plt.grid(True)
plt.tight_layout()
plt.savefig("reward_over_time.png")
plt.show()

# Plot cpu_offset and interactive_offset over time
plt.figure(figsize=(10, 4))
plt.plot(df["episode"], df["cpu_offset"], label="CPU Offset", marker="s")
plt.plot(df["episode"], df["interactive_offset"], label="Interactive Offset", marker="^")
plt.title("Offset Adjustments over Time")
plt.xlabel("Episode")
plt.ylabel("Offset Value")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("offsets_over_time.png")
plt.show()

# Count action occurrences
action_counts = df["action"].value_counts()

# Plot
plt.figure(figsize=(8, 4))
bars = plt.bar(action_counts.index, action_counts.values, color="#4C72B0", edgecolor="black", width=0.5)

# Add text labels on top of bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 20, f"{int(height)}", ha='center', va='bottom', fontsize=10)

# Formatting
plt.title("Action Frequency (Scenario 2)", fontsize=14)
plt.xlabel("Action", fontsize=12)
plt.ylabel("Count", fontsize=12)
plt.xticks(rotation=10, ha='center', fontsize=10)
plt.yticks(fontsize=10)
plt.grid(False, axis="y", linestyle="--", linewidth=0.6)
plt.tight_layout()

# Save high-quality figure
plt.savefig("action_frequency_scenario2.png", dpi=300)
plt.show()




