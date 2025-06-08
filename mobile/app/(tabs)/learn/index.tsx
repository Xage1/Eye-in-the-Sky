import { FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';

const learningPaths = [
    {
        id: 'stars',
        title: 'Stars & Constellations',
        icon: 'star.fill',
        description: 'Learn about different types of stars and constellations',
        lessons: [
            { id: 'star-lifecycle', title: 'Life Cycle of Stars' },
            { id: 'constellations', title: 'Major Constellations' },
            { id: 'star-types', title: 'Types of Stars' },
        ],
    },
    {
        id: 'planets',
        title: 'Planets & Solar System',
        icon: 'globe.americas.fill',
        description: 'Explore our solar system and planetary science',
        lessons: [
            { id: 'solar-system', title: 'Our Solar System' },
            { id: 'planet-types', title: 'Types of Planets' },
            { id: 'exoplanets', title: 'Exoplanets' },
        ],
    },
    // More paths...
];

export default function LearnScreen() {
    const colorScheme = useColorScheme();

    const renderPath = ({ item }: { item: typeof learningPaths[0] }) => (
        <ThemedView style={styles.pathCard}>
            <View style={styles.pathHeader}>
                <IconSymbol
                    name={item.icon}
                    size={24}
                    color={Colors[colorScheme].tint}
                />
                <ThemedText type="title" style={styles.pathTitle}>
                    {item.title}
                </ThemedText>
            </View>
            <ThemedText style={styles.pathDescription}>
                {item.description}
            </ThemedText>
            <View style={styles.lessonsContainer}>
                {item.lessons.map((lesson) => (
                    <TouchableOpacity
                        key={lesson.id}
                        style={styles.lessonItem}
                        onPress={() => console.log('Navigate to lesson', lesson.id)}
                    >
                        <ThemedText>{lesson.title}</ThemedText>
                        <IconSymbol
                            name="chevron.right"
                            size={16}
                            color={Colors[colorScheme].icon}
                        />
                    </TouchableOpacity>
                ))}
            </View>
        </ThemedView>
    );

    return (
        <ThemedView style={styles.container}>
            <FlatList
                data={learningPaths}
                renderItem={renderPath}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
            />
        </ThemedView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 16,
    },
    listContent: {
        paddingBottom: 20,
        gap: 16,
    },
    pathCard: {
        padding: 16,
        borderRadius: 8,
        gap: 12,
    },
    pathHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    pathTitle: {
        flex: 1,
    },
    pathDescription: {
        fontSize: 14,
        color: '#666',
    },
    lessonsContainer: {
        gap: 8,
        marginTop: 8,
    },
    lessonItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 6,
        backgroundColor: 'rgba(0,0,0,0.05)',
    },
});