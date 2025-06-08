import { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber/native';
import { Stars, Sky, Text3D, OrbitControls } from '@react-three/drei/native';
import { View, StyleSheet, useWindowDimensions, TouchableOpacity } from 'react-native';
import * as Location from 'expo-location';
import { useAnimatedSensor, SensorType } from 'react-native-reanimated';
import { useStars } from '@/hooks/useStars';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import { getConstellationForPosition } from '@/utils/astronomyUtils';

export default function SkyGuideScreen() {
    const { width, height } = useWindowDimensions();
    const colorScheme = useColorScheme();
    const [location, setLocation] = useState<Location.LocationObject | null>(null);
    const [selectedStar, setSelectedStar] = useState<any>(null);
    const [date, setDate] = useState(new Date());
    const [nightMode, setNightMode] = useState(false);

    const animatedSensor = useAnimatedSensor(SensorType.GYROSCOPE, {
        interval: 100,
    });

    useEffect(() => {
        (async () => {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                console.error('Permission to access location was denied');
                return;
            }

            let location = await Location.getCurrentPositionAsync({});
            setLocation(location);
        })();
    }, []);

    const { stars, constellations } = useStars(location, date);

    const StarSphere = () => {
        const meshRef = useRef<any>();

        useFrame(() => {
            if (meshRef.current) {
                const { x, y, z } = animatedSensor.sensor.value;
                meshRef.current.rotation.x += y * 0.01;
                meshRef.current.rotation.y += x * 0.01;
            }
        });

        return (
            <group ref={meshRef}>
                <Stars
                    radius={100}
                    depth={50}
                    count={5000}
                    factor={4}
                    saturation={0}
                    fade
                    speed={1}
                />
                {stars.map((star: any) => (
                    <mesh
                        key={star.id}
                        position={[star.x, star.y, star.z]}
                        onClick={() => setSelectedStar(star)}
                    >
                        <sphereGeometry args={[star.size, 16, 16]} />
                        <meshBasicMaterial color={star.color} />
                    </mesh>
                ))}
                {constellations.map((constellation: any) => (
                    <group key={constellation.name}>
                        {constellation.stars.map((star: any, index: number) => (
                            <line
                                key={index}
                                points={[star.from, star.to]}
                                color="white"
                                lineWidth={1}
                            />
                        ))}
                        <Text3D
                            position={constellation.labelPosition}
                            size={0.5}
                            height={0.02}
                            curveSegments={12}
                            bevelEnabled
                            bevelThickness={0.02}
                            bevelSize={0.02}
                            bevelOffset={0}
                            bevelSegments={5}
                        >
                            {constellation.name}
                            <meshBasicMaterial color="white" />
                        </Text3D>
                    </group>
                ))}
            </group>
        );
    };

    return (
        <ThemedView style={styles.container}>
            <View style={styles.header}>
                <ThemedText type="title">Sky Guide</ThemedText>
                <TouchableOpacity onPress={() => setNightMode(!nightMode)}>
                    <IconSymbol
                        name={nightMode ? 'lightbulb.fill' : 'moon.fill'}
                        size={24}
                        color={nightMode ? '#ff5555' : Colors[colorScheme].tint}
                    />
                </TouchableOpacity>
            </View>

            <View style={[styles.canvasContainer, { backgroundColor: nightMode ? '#000011' : '#f0f0f0' }]}>
                <Canvas style={{ width, height: height - 200 }}>
                    <ambientLight intensity={nightMode ? 0.1 : 0.5} />
                    <pointLight position={[10, 10, 10]} />
                    <StarSphere />
                    <OrbitControls enableZoom={false} />
                </Canvas>
            </View>

            {selectedStar && (
                <StarInfoCard
                    star={selectedStar}
                    onClose={() => setSelectedStar(null)}
                    nightMode={nightMode}
                />
            )}
        </ThemedView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
    },
    canvasContainer: {
        flex: 1,
    },
});