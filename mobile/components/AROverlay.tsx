import { Camera, CameraType } from 'expo-camera';
import { View, StyleSheet, Text, TouchableOpacity } from 'react-native';
import { useEffect, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber/native';
import { useAnimatedSensor, SensorType } from 'react-native-reanimated';
import { useStars } from '@/hooks/useStars';
import { ThemedText } from '@/components/ThemedText';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';

export function AROverlay() {
    const [permission, requestPermission] = Camera.useCameraPermissions();
    const [type, setType] = useState(CameraType.back);
    const cameraRef = useRef<Camera>(null);
    const [arEnabled, setArEnabled] = useState(false);
    const colorScheme = useColorScheme();

    if (!permission) {
        return <View />;
    }

    if (!permission.granted) {
        return (
            <View style={styles.permissionContainer}>
                <ThemedText style={styles.permissionText}>
                    We need your permission to show the camera
                </ThemedText>
                <TouchableOpacity onPress={requestPermission} style={styles.permissionButton}>
                    <ThemedText style={styles.permissionButtonText}>Grant Permission</ThemedText>
                </TouchableOpacity>
            </View>
        );
    }

    const toggleCameraType = () => {
        setType(current =>
            current === CameraType.back ? CameraType.front : CameraType.back
        );
    };

    return (
        <View style={styles.container}>
            {arEnabled ? (
                <>
                    <Camera style={styles.camera} type={type} ref={cameraRef}>
                        <ARScene />
                    </Camera>
                    <View style={styles.controls}>
                        <TouchableOpacity
                            style={styles.controlButton}
                            onPress={toggleCameraType}
                        >
                            <IconSymbol
                                name="arrow.triangle.2.circlepath.camera"
                                size={24}
                                color={Colors[colorScheme].tint}
                            />
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={styles.controlButton}
                            onPress={() => setArEnabled(false)}
                        >
                            <IconSymbol
                                name="xmark"
                                size={24}
                                color={Colors[colorScheme].tint}
                            />
                        </TouchableOpacity>
                    </View>
                </>
            ) : (
                <TouchableOpacity
                    style={styles.arButton}
                    onPress={() => setArEnabled(true)}
                >
                    <IconSymbol
                        name="arkit"
                        size={32}
                        color={Colors[colorScheme].tint}
                    />
                    <ThemedText style={styles.arButtonText}>Start AR Mode</ThemedText>
                </TouchableOpacity>
            )}
        </View>
    );
}

function ARScene() {
    const animatedSensor = useAnimatedSensor(SensorType.GYROSCOPE);
    const { stars, constellations } = useStars();

    const groupRef = useRef<any>();

    useFrame(() => {
        if (groupRef.current) {
            const { x, y, z } = animatedSensor.sensor.value;
            groupRef.current.rotation.x = y;
            groupRef.current.rotation.y = x;
            groupRef.current.rotation.z = z;
        }
    });

    return (
        <Canvas style={{ flex: 1 }}>
            <group ref={groupRef}>
                {stars.map((star) => (
                    <mesh key={star.id} position={[star.x, star.y, star.z]}>
                        <sphereGeometry args={[star.size, 16, 16]} />
                        <meshBasicMaterial color={star.color} />
                    </mesh>
                ))}
                {constellations.map((constellation) => (
                    <group key={constellation.name}>
                        {constellation.stars.map((line, idx) => (
                            <line key={idx}>
                                <bufferGeometry
                                    attributes={{
                                        position: new Float32Array([...line.from, ...line.to]),
                                    }}
                                />
                                <lineBasicMaterial color="white" linewidth={1} />
                            </line>
                        ))}
                    </group>
                ))}
            </group>
        </Canvas>
    );
}

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        bottom: 20,
        right: 20,
        zIndex: 100,
    },
    camera: {
        width: 200,
        height: 300,
        borderRadius: 20,
        overflow: 'hidden',
    },
    controls: {
        position: 'absolute',
        bottom: 10,
        left: 0,
        right: 0,
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 20,
    },
    controlButton: {
        backgroundColor: 'rgba(0,0,0,0.5)',
        padding: 10,
        borderRadius: 50,
    },
    arButton: {
        backgroundColor: 'rgba(0,0,0,0.7)',
        padding: 15,
        borderRadius: 50,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
    },
    arButtonText: {
        color: 'white',
        fontWeight: 'bold',
    },
    permissionContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    permissionText: {
        textAlign: 'center',
        marginBottom: 20,
    },
    permissionButton: {
        backgroundColor: '#0a7ea4',
        padding: 15,
        borderRadius: 10,
    },
    permissionButtonText: {
        color: 'white',
        fontWeight: 'bold',
    },
});