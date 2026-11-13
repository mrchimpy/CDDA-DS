// Test-only bridge and game/widget substitutes; not the real CDDA needs evaluator.
#include "ds_hud.h"
#include <cassert>
#include <string>

#if defined(NEEDS_JNI_TEST)
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_NeedsHostTest_seed( JNIEnv *, jclass, jint mode )
{
    if( mode == 0 ) { ds_hud::end_session(); return; }
    if( mode == 1 ) { ds_hud::begin_session(); return; }
    if( !ds_hud::read().active ) { ds_hud::begin_session(); }
    ds_hud::body_health health;
    health.current.fill( 40 ); health.maximum.fill( 80 );
    ds_hud::core_status core;
    core.strength = 9; core.dexterity = 7; core.intelligence = 5;
    core.perception = 11; core.speed = 90; core.focus = 125;
    core.movement_mode = "walk (W)";
    ds_hud::activity_status status;
    for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
        status.available[i] = true; status.text[i] = "field " + std::to_string( i );
    }
    status.text[26] = "Satisfied"; status.text[27] = "Slaked"; status.text[28] = "Tired";
    if( mode == 3 ) {
        status.text[26] = "Hungry"; status.text[27] = "Very thirsty"; status.text[28] = "Dead Tired";
    }
    if( mode == 4 || mode == 7 ) {
        for( int i = 26; i < 29; ++i ) { status.text[i] = mode == 4 ? "" : "  \t\n"; }
    }
    if( mode == 5 ) {
        for( int i = 26; i < 29; ++i ) { status.available[i] = false; }
    }
    if( mode == 6 ) {
        status.text[26] = "Faim \xc3\xa9 \xf0\x9f\x9a\x80";
        status.text[27] = std::string( 1000, 'T' );
        status.text[28] = std::string( "A\0B", 3 );
    }
    ds_hud::publish( 50, 100, health, core, status );
}
#else
#include <atomic>
#include <map>
#include <thread>
#include <vector>
struct bodypart_id { explicit bodypart_id( const char * ) {} };
struct movement_mode {
    std::string name() const { return "walk"; }
    char panel_letter() const { return 'W'; }
};
struct avatar {
    int get_part_hp_cur( const bodypart_id & ) const { return 40; }
    int get_part_hp_max( const bodypart_id & ) const { return 80; }
    int get_str() const { return 9; } int get_dex() const { return 7; }
    int get_int() const { return 5; } int get_per() const { return 11; }
    int get_speed() const { return 90; } int get_focus() const { return 125; }
    int get_stamina() const { return 50; } int get_stamina_max() const { return 100; }
    const movement_mode *current_movement_mode() const { static movement_mode m; return &m; }
};
struct widget;
struct widget_id {
    std::string id;
    explicit widget_id( const char *s ) : id( s ) {}
    bool is_valid() const;
    const widget &obj() const;
    bool operator!=( const widget_id &other ) const { return id != other.id; }
};
struct widget {
    std::string text;
    int local_draws = 0;
    std::string show( const avatar &, int width ) { assert( width == 80 ); ++local_draws; return text; }
    std::vector<widget_id> widgets( bool ) const { return {}; }
};
static std::map<std::string, widget> registry;
bool widget_id::is_valid() const { return registry.count( id ) != 0; }
const widget &widget_id::obj() const { return registry.at( id ); }
static std::string remove_color_tags( std::string text ) {
    for( std::size_t p = text.find( '<' ); p != std::string::npos; p = text.find( '<' ) ) {
        const auto end = text.find( '>', p ); assert( end != std::string::npos );
        text.erase( p, end - p + 1 );
    }
    return text;
}
struct game {
    avatar u;
    void draw_panels( bool force_draw ) {
        ( void )force_draw;
        // NEEDS_CAPTURE_HOOK
    }
};
int main() {
    static_assert( ds_hud::activity_field_count == 29, "appended needs fields" );
    static_assert( ds_hud::wire_field_count == 53, "wire dimensions" );
    registry["hunger_desc_label"].text = "<color_red>Hungry</color>";
    registry["thirst_desc_label"].text = "Thirsty";
    registry["sleepiness_desc_label"].text = "Tired";
    registry["wielding_desc"].text = "retained upstream/wire";
    registry["oxygen_classic_layout"].text = "";
    registry["oxygen_graph_classic"].text = "|||||";
    game g;
    ds_hud::begin_session(); g.draw_panels( true );
    auto first = ds_hud::read();
    assert( first.activity.text[26] == "Hungry" && first.activity.text[27] == "Thirsty" );
    assert( first.activity.text[28] == "Tired" && first.activity.available[28] );
    assert( first.activity.text[12] == "retained upstream/wire" );
    assert( first.activity.available[19] && first.activity.text[19].empty() );
    registry["hunger_desc_label"].text = "Satisfied";
    registry["thirst_desc_label"].text = "";
    registry.erase( "sleepiness_desc_label" );
    g.draw_panels( false );
    const auto changed = ds_hud::read();
    assert( changed.activity.text[26] == "Satisfied" );
    assert( changed.activity.text[27].empty() && changed.activity.available[27] );
    assert( !changed.activity.available[28] && changed.activity.text[28].empty() );
    assert( first.activity.text[26] == "Hungry" );
    for( const auto &entry : registry ) { assert( entry.second.local_draws == 0 ); }
    first.activity.text[26] = "reader mutation";
    assert( ds_hud::read().activity.text[26] == "Satisfied" );
    ds_hud::end_session(); g.draw_panels( true );
    assert( !ds_hud::read().active && ds_hud::read().activity.text[26].empty() );
    ds_hud::begin_session();
    assert( !ds_hud::read().ready && ds_hud::read().activity.text[26].empty() );
    std::atomic<bool> finished{false};
    std::thread writer( [&]() {
        for( int tag = 1; tag <= 1000; ++tag ) {
            ds_hud::activity_status data;
            data.available.fill( true ); data.text.fill( std::to_string( tag ) );
            ds_hud::publish( tag, 2000, {}, {}, data );
        }
        finished = true;
    } );
    do {
        const auto copy = ds_hud::read();
        if( copy.ready ) {
            for( const auto &text : copy.activity.text ) { assert( text == std::to_string( copy.current ) ); }
        }
    } while( !finished );
    writer.join(); ds_hud::end_session();
}
#endif
