export type Cat = {
    id: string;
    name: string;
    breed: string;
    status: 'fed' | 'hungry' | 'eating';
    lastFedTime: string; // ISO string
    avatar: string;
    description: string;
};

export type FeedingEvent = {
    id: string;
    catId: string;
    timestamp: string;
    type: 'food' | 'water';
    amount: number; // grams for food, ml for water
    duration: number; // seconds
    thumbnail?: string;
};

export type DailyStats = {
    date: string;
    count: number;
};

export const MOCK_CATS: Cat[] = [
    {
        id: 'c1',
        name: 'Luna',
        breed: 'Bombay',
        status: 'fed',
        lastFedTime: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 mins ago
        avatar: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=400&fit=crop',
        description: 'Mysterious night prowler. Loves tuna.'
    },
    {
        id: 'c2',
        name: 'Milo',
        breed: 'Orange Tabby',
        status: 'hungry',
        lastFedTime: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), // 5 hours ago
        avatar: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=400&h=400&fit=crop',
        description: 'Always hungry. Will meow for food.'
    },
    {
        id: 'c3',
        name: 'Oliver',
        breed: 'British Shorthair',
        status: 'fed',
        lastFedTime: new Date(Date.now() - 1000 * 60 * 120).toISOString(), // 2 hours ago
        avatar: 'https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=400&h=400&fit=crop',
        description: 'Aristocratic and picky eater.'
    },
    {
        id: 'c4',
        name: 'Leo',
        breed: 'Siamese',
        status: 'eating',
        lastFedTime: new Date().toISOString(), // Just now
        avatar: 'https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?w=400&h=400&fit=crop',
        description: 'Vocal and demanding. Loves chicken.'
    },
    {
        id: 'c5',
        name: 'Bella',
        breed: 'Calico',
        status: 'fed',
        lastFedTime: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 mins ago
        avatar: 'https://images.unsplash.com/photo-1529778873920-4da4926a7071?w=400&h=400&fit=crop',
        description: 'Sweet and gentle. Eats slowly.'
    }
];

export const MOCK_FEEDING_EVENTS: FeedingEvent[] = [
    { id: 'e1', catId: 'c4', timestamp: new Date().toISOString(), type: 'food', amount: 15, duration: 120 },
    { id: 'e2', catId: 'c1', timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), type: 'food', amount: 45, duration: 300 },
    { id: 'e3', catId: 'c5', timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), type: 'water', amount: 30, duration: 240 },
    { id: 'e4', catId: 'c3', timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(), type: 'food', amount: 50, duration: 350 },
    { id: 'e5', catId: 'c2', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), type: 'water', amount: 60, duration: 400 },
    { id: 'e6', catId: 'c4', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), type: 'water', amount: 45, duration: 180 },
];

export const MOCK_STATS = {
    todayCount: 12,
    activeCats: 4,
    bowlStatus: '75%', // 3/4 full
    lastFed: '2 min ago'
};
