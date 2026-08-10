// Placeholder for Simulator Service
export const connect = () => {
    console.log("Connecting to Simulator...");
    return true;
};

export const disconnect = () => {
    console.log("Disconnecting from Simulator...");
};

export const sendCommand = (command, payload) => {
    console.log(`Sending command ${command}:`, payload);
};

export const receiveTelemetry = (callback) => {
    // Mock implementation
    setInterval(() => {
        callback({
            gps: { lat: 34.0522 + Math.random() * 0.001, lng: -118.2437 + Math.random() * 0.001 },
            altitude: 120 + Math.random() * 2,
            heading: Math.floor(Math.random() * 360),
            speed: 15 + Math.random(),
        });
    }, 1000);
};

export const receiveDetections = (callback) => {
    // Mock
};

export const receiveMap = (callback) => {
    // Mock
};
