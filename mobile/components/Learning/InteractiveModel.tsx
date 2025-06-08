import { Canvas, useFrame } from '@react-three/fiber/native';
import { OrbitControls, Text3D } from '@react-three/drei/native';
import { View, StyleSheet } from 'react-native';
import { useRef, useState } from 'react';

interface InteractiveModelProps {
    model: string;
    style?: any;
}

const MODELS: Record<string, JSX.Element> = {
    'star-lifecycle': <StarLifecycleModel />,
    // Other models...
};

export function InteractiveModel({ model, style }: InteractiveModelProps) {
    const ModelComponent = MODELS[model] || null;

    return (
        <View style={[styles.container, style]}>
            <Canvas>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} />
                {ModelComponent}
                <OrbitControls enableZoom={true} />
            </Canvas>
        </View>
    );
}

function StarLifecycleModel() {
    const groupRef = useRef<any>();
    const [stage, setStage] = useState(0);

    useFrame(() => {
        if (groupRef.current) {
            groupRef.current.rotation.y += 0.01;
        }
    });

    return (
        <group ref={groupRef}>
            {/* Nebula */}
            {stage === 0 && (
                <mesh>
                    <sphereGeometry args={[1, 32, 32]} />
                    <meshStandardMaterial color="#9bb0ff" transparent opacity={0.5} />
                    <Text3D position={[0, 1.5, 0]} size={0.2}>
                        Nebula
                        <meshBasicMaterial color="white" />
                    </Text3D>
                </mesh>
            )}

            {/* Protostar */}
            {stage === 1 && (
                <mesh>
                    <sphereGeometry args={[0.5, 32, 32]} />
                    <meshStandardMaterial color="#ff8b60" emissive="#ff8b60" emissiveIntensity={0.5} />
                    <Text3D position={[0, 1, 0]} size={0.2}>
                        Protostar
                        <meshBasicMaterial color="white" />
                    </Text3D>
                </mesh>
            )}

            {/* More stages... */}
        </group>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
        borderRadius: 8,
        overflow: 'hidden',
    },
});