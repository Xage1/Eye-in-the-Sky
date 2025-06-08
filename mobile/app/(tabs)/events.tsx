import { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import axios from 'axios';
import { format, parseISO } from 'date-fns';
import { ThemedView } from '@/components/ThemedView';
import { ThemedText } from '@/components/ThemedText';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { useColorScheme } from '@/hooks/useColorScheme';
import * as Location from 'expo-location';

interface CelestialEvent {
    id: string;
    name: string;
    date: string;
    type: 'meteor' | 'eclipse' | 'conjunction' | 'iss' | 'other';
    description: string;
    visibility: 'good' | 'fair' | 'poor';
}

export default function EventsScreen() {
    const [events, setEvents] = useState<CelestialEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [location, setLocation] = useState<Location.LocationObject | null>(null);
    const [error, setError] = useState<string | null>(null);
    const colorScheme = useColorScheme();

    useEffect(() => {
        (async () => {
            try {
                const { status } = await Location.requestForegroundPermissionsAsync();
                if (status !== 'granted') {
                    setError('Location permission not granted');
                    return;
                }

                const location = await Location.getCurrentPositionAsync({});
                setLocation(location);

                const response = await axios.get('https://api.astronomyapi.com/v2/events', {
                    params: {
                        lat: location.coords.latitude,
                        lon: location.coords.longitude,
                        date: format(new Date(), 'yyyy-MM-dd'),
                        days: 30
                    },
                    headers: {
                        'Authorization': `Bearer YOUR_API_KEY`
                    }
                });

                const formattedEvents = response.data.events.map((event: any) => ({
                    id: event.id,
                    name: event.name,
                    date: event.date,
                    type: event.type,
                    description: event.description,
                    visibility: calculateVisibility(event.conditions)
                }));

                setEvents(formattedEvents);
            } catch (err) {
                console.error('Error fetching events:', err);
                setError('Failed to fetch events');
                // Fallback to mock data if API fails
                setEvents(getMockEvents());
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const calculateVisibility = (conditions: any): 'good' | 'fair' | 'poor' => {
        // Simplified visibility calculation
        if (conditions.cloudCover < 30) return 'good';
        if (conditions.cloudCover < 70) return 'fair';
        return 'poor';
    };

    const getMockEvents = (): CelestialEvent[] => {
        return [
            {
                id: '1',
                name: 'Perseid Meteor Shower',
                date: '2023-08-12T00:00:00Z',
                type: 'meteor',
                description: 'Annual meteor shower with up to 100 meteors per hour',
                visibility: 'good'
            },
            // More mock events...
        ];
    };

    const renderEvent = ({ item }: { item: CelestialEvent }) => (
        <ThemedView style={styles.eventCard}>
            <View style={styles.eventHeader}>
                <IconSymbol
                    name={getIconForEventType(item.type)}
                    size={24}
                    color={Colors[colorScheme].tint}
                />
                <ThemedText type="defaultSemiBold" style={styles.eventName}>
                    {item.name}
                </ThemedText>
                <ThemedText style={styles.eventDate}>
                    {format(parseISO(item.date), 'MMM d, h:mm a')}
                </ThemedText>
            </View>
            <ThemedText style={styles.eventDescription}>
                {item.description}
            </ThemedText>
            <View style={[
                styles.visibilityBadge,
                {
                    backgroundColor: getVisibilityColor(item.visibility),
                    borderColor: Colors[colorScheme].tint
                }
            ]}>
                <ThemedText style={styles.visibilityText}>
                    Visibility: {item.visibility}
                </ThemedText>
            </View>
        </ThemedView>
    );

    return (
        <ThemedView style={styles.container}>
            {error && (
                <ThemedView style={styles.errorContainer}>
                    <ThemedText style={styles.errorText}>{error}</ThemedText>
                </ThemedView>
            )}

            <FlatList
                data={events}
                renderItem={renderEvent}
                keyExtractor={(item) => item.id}
                ListEmptyComponent={
                    loading ? (
                        <ThemedText>Loading events...</ThemedText>
                    ) : (
                        <ThemedText>No upcoming events found</ThemedText>
                    )
                }
                contentContainerStyle={styles.listContent}
            />
        </ThemedView>
    );
}

function getIconForEventType(type: string): string {
    switch (type) {
        case 'meteor': return 'meteor';
        case 'eclipse': return 'moon';
        case 'iss': return 'airplane';
        case 'conjunction': return 'circle.grid.2x2';
        default: return 'star';
    }
}

function getVisibilityColor(visibility: string): string {
    switch (visibility) {
        case 'good': return '#4CAF50';
        case 'fair': return '#FFC107';
        case 'poor': return '#F44336';
        default: return '#9E9E9E';
    }
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
    eventCard: {
        padding: 16,
        borderRadius: 8,
        gap: 8,
    },
    eventHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    eventName: {
        flex: 1,
    },
    eventDate: {
        color: '#666',
    },
    eventDescription: {
        fontSize: 14,
    },
    visibilityBadge: {
        alignSelf: 'flex-start',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 1,
        marginTop: 8,
    },
    visibilityText: {
        fontSize: 12,
        color: 'white',
    },
    errorContainer: {
        backgroundColor: '#FFEBEE',
        padding: 16,
        borderRadius: 8,
        marginBottom: 16,
    },
    errorText: {
        color: '#D32F2F',
    },
});