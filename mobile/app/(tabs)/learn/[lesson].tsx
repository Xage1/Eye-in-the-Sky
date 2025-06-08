import { useLocalSearchParams } from 'expo-router';
import { StyleSheet, ScrollView } from 'react-native';
import Markdown from 'react-native-markdown-display';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { InteractiveModel } from '@/components/Learning/InteractiveModel';
import { QuizButton } from '@/components/Learning/QuizButton';

const lessonContent: Record<string, string> = {
    'star-lifecycle': `
# Life Cycle of Stars

Stars are born in **nebulas** - giant clouds of gas and dust. 

## Stages of a Star's Life:

1. **Nebula**: Cloud of gas and dust
2. **Protostar**: Gravity pulls material together
3. **Main Sequence**: Star shines by nuclear fusion (like our Sun)
4. **Red Giant/Supergiant**: Star expands as fuel runs out
5. **Final Stage**:
   - Small stars become **white dwarfs**
   - Large stars explode as **supernovae** and become **neutron stars** or **black holes**

\`\`\`mermaid
graph TD
    A[Nebula] --> B[Protostar]
    B --> C[Main Sequence Star]
    C --> D[Red Giant]
    D --> E[White Dwarf]
    C --> F[Supergiant]
    F --> G[Supernova]
    G --> H[Neutron Star or Black Hole]
\`\`\`
`,
    // More lesson content...
};

export default function LessonScreen() {
    const { lesson } = useLocalSearchParams();
    const content = lessonContent[lesson as string] || 'Lesson not found';

    return (
        <ThemedView style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Markdown>{content}</Markdown>

                {lesson === 'star-lifecycle' && (
                    <InteractiveModel
                        model="star-lifecycle"
                        style={styles.model}
                    />
                )}
            </ScrollView>

            <QuizButton lessonId={lesson as string} />
        </ThemedView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
        gap: 20,
    },
    model: {
        height: 300,
        marginVertical: 20,
    },
});