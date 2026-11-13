#pragma once
#include <string>
struct bodypart_id { explicit bodypart_id( const char * ) {} };
struct movement {
    std::string name() const { return "walk"; }
    char panel_letter() const { return 'W'; }
};
struct avatar {
    movement mode;
    int sample = 0;
    int get_part_hp_cur( const bodypart_id & ) const { return 20; }
    int get_part_hp_max( const bodypart_id & ) const { return 80; }
    int get_stamina() const { return 35; }
    int get_stamina_max() const { return 100; }
    int get_str() const { return 5; }
    int get_dex() const { return 6; }
    int get_int() const { return 7; }
    int get_per() const { return 8; }
    int get_speed() const { return 90; }
    int get_focus() const { return 140; }
    const movement *current_movement_mode() const { return &mode; }
};
struct game { avatar u; void draw_panels( bool force_draw ); };
