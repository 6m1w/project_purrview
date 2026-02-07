// Database types for PurrView tables
// Can be regenerated with: supabase gen types typescript

export type Database = {
  public: {
    Tables: {
      purrview_cats: {
        Row: {
          id: string;
          name: string;
          description: string | null;
          reference_photos: string[] | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          description?: string | null;
          reference_photos?: string[] | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string | null;
          reference_photos?: string[] | null;
          created_at?: string;
        };
      };
      purrview_feeding_events: {
        Row: {
          id: string;
          cat_id: string | null;
          bowl_id: string | null;
          started_at: string;
          ended_at: string | null;
          food_level_before: string | null;
          food_level_after: string | null;
          estimated_portion: string | null;
          confidence: number | null;
          notes: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          cat_id?: string | null;
          bowl_id?: string | null;
          started_at: string;
          ended_at?: string | null;
          food_level_before?: string | null;
          food_level_after?: string | null;
          estimated_portion?: string | null;
          confidence?: number | null;
          notes?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          cat_id?: string | null;
          bowl_id?: string | null;
          started_at?: string;
          ended_at?: string | null;
          food_level_before?: string | null;
          food_level_after?: string | null;
          estimated_portion?: string | null;
          confidence?: number | null;
          notes?: string | null;
          created_at?: string;
        };
      };
      purrview_frames: {
        Row: {
          id: string;
          feeding_event_id: string | null;
          captured_at: string;
          frame_url: string;
          analysis: Record<string, unknown> | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          feeding_event_id?: string | null;
          captured_at: string;
          frame_url: string;
          analysis?: Record<string, unknown> | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          feeding_event_id?: string | null;
          captured_at?: string;
          frame_url?: string;
          analysis?: Record<string, unknown> | null;
          created_at?: string;
        };
      };
      purrview_food_bowls: {
        Row: {
          id: string;
          name: string | null;
          roi_x1: number | null;
          roi_y1: number | null;
          roi_x2: number | null;
          roi_y2: number | null;
          is_active: boolean | null;
        };
        Insert: {
          id: string;
          name?: string | null;
          roi_x1?: number | null;
          roi_y1?: number | null;
          roi_x2?: number | null;
          roi_y2?: number | null;
          is_active?: boolean | null;
        };
        Update: {
          id?: string;
          name?: string | null;
          roi_x1?: number | null;
          roi_y1?: number | null;
          roi_x2?: number | null;
          roi_y2?: number | null;
          is_active?: boolean | null;
        };
      };
    };
  };
};

// Convenience type aliases
export type Cat = Database["public"]["Tables"]["purrview_cats"]["Row"];
export type FeedingEvent = Database["public"]["Tables"]["purrview_feeding_events"]["Row"];
export type Frame = Database["public"]["Tables"]["purrview_frames"]["Row"];
export type FoodBowl = Database["public"]["Tables"]["purrview_food_bowls"]["Row"];
