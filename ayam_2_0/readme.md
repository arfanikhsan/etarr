#Ayam Lepas (Loose Chicken)
Ayam Lepas is an interactive mixed-media installation and the sequel to a previous harvest-themed project. It explores the chaotic intersection of nature and urban spatial compression through real-time reactive audio and live 3D visual feeds.
Deck persentation link : https://canva.link/1c6okrjl0gxkar5

## 📖 Concept & Background
The Prequel:
The first installation celebrated the Indonesian harvest moon. It featured a traditional rattan chicken run surrounded by chicken balloons, with one equipped with an ultrasonic sensor (HC-SR04) and ESP32 to trigger audio upon audience encounters.

The Sequel (Ayam Lepas):
In this second iteration, the narrative shifts to an urban environment. A chicken mistakenly enters a human space, creating chaos. Because urban areas lack wide fields, the flock roams freely in an alien atmosphere.

Epistemological Layer:
A helium-filled chicken balloon floats slightly above the enclosed room, serving as an instantiation of the chicken's aspiration to fly—a physical ability omitted by evolution and permanently denied by spatial compression.

Audience interaction inside the room (punching, catching, rotating, or releasing the balloon) creates collective chaos. These interactions are tracked to generate reactive soundscapes that reflect how the "chicken" is being treated, which are then translated into a live 3D visualization.

## ⚙️ Technical Architecture
This project relies on a portable, wireless embedded system inside the balloon that communicates with audio and visual software over a local network.

Hardware
Microcontroller: ESP32 (Portable, Wi-Fi enabled)

Power: Li-Po Battery

Sensor: LSM6D3S IMU (Accelerometer & Gyroscope)

Filters applied: Low-pass filter for clean data.

Tracked parameters: Roll, Pitch, Yaw, and built-in events (Raise, Tap, Double Tap, Fall).

Software
Audio Generation: Max/MSP

3D Visuals: Rhino 3D & Grasshopper (using the Firefly plugin)

Communication Protocol: OSC (Open Sound Control) via UDP

## 🔄 Data Pipeline
Motion Tracking: The ESP32 reads continuous orientation data and physical impact events from the LSM6D3S IMU.

Wireless Transmission: The filtered data is sent as real-time OSC signals over a local Wi-Fi network.

Audio Processing (Max/MSP): Max/MSP receives the OSC signals via a udpreceive component. The movement and impact parameters dictate the reactive sound output.

Live Visuals (Rhino/Grasshopper): Max/MSP sends the generated audio data out via a different port. Grasshopper (Firefly) receives this feed to drive live, reactive 3D visuals directly within the Rhino viewport.
