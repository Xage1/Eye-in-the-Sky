package com.eye.sky.net

/**
 * Set BASE_URL to your machine's IP when testing on a physical device.
 *
 * How to find your PC's IP:
 *   Windows PowerShell: ipconfig | findstr IPv4
 *   Look for the IP on the same WiFi network as your phone.
 *
 * Examples:
 *   Emulator    → "http://10.0.2.2:8000/"
 *   Physical    → "http://192.168.1.105:8000/"   ← your PC's WiFi IP
 *   USB tunnel  → "http://localhost:8000/"  (after: adb reverse tcp:8000 tcp:8000)
 */
object NetworkConfig {
    // USB tunnel is the most reliable — run this once:
    // adb reverse tcp:8000 tcp:8000
    // Then set to localhost
    const val BASE_URL = "http://localhost:8000/"
}