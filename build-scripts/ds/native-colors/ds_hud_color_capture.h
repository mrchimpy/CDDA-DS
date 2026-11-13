#ifndef CATA_SRC_DS_HUD_COLOR_CAPTURE_H
#define CATA_SRC_DS_HUD_COLOR_CAPTURE_H

#include "ds_hud_colors.h"
#include "avatar.h"
#include "color.h"
#include "cursesport.h"
#include "sdltiles.h"
#include "widget.h"

namespace ds_hud
{
inline std::uint32_t palette_argb( int index )
{
    if( index < 0 || static_cast<std::size_t>( index ) >= windowsPalette.size() ) {
        return 0xff969696;
    }
    const auto &color = windowsPalette[index];
    return 0xff000000u | ( static_cast<std::uint32_t>( color.r ) << 16 ) |
           ( static_cast<std::uint32_t>( color.g ) << 8 ) | color.b;
}

inline ink native_ink( const nc_color &color )
{
    const int index = color.to_color_pair_index();
    if( index < 0 || static_cast<std::size_t>( index ) >= cata_cursesport::colorpairs.size() ) {
        return {};
    }
    const auto &pair = cata_cursesport::colorpairs[index];
    // Exactly the foreground/background index rules in catacurses::wattron.
    // A_BLINK selects the bright background; it is not an Android animation.
    return {palette_argb( static_cast<int>( pair.FG ) + ( color.is_bold() ? 8 : 0 ) ),
            palette_argb( static_cast<int>( pair.BG ) + ( color.is_blink() ? 8 : 0 ) )};
}

inline styled_text native_styled_text( const std::string &marked, ink neutral )
{
    return parse_markup( marked, neutral, []( std::string_view candidate ) {
        const color_tag_parse_result tag = get_color_from_tag( candidate, report_color_error::no );
        if( tag.type == color_tag_parse_result::open_color_tag ) {
            return parsed_tag{parsed_tag::kind::open, native_ink( tag.color )};
        }
        if( tag.type == color_tag_parse_result::close_color_tag ) {
            return parsed_tag{parsed_tag::kind::close, {}};
        }
        return parsed_tag{};
    } );
}

inline ink native_number_ink( const avatar &u, const char *name, color_status &colors )
{
    const widget_id id( name );
    if( !id.is_valid() ) {
        colors.complete = false;
        return colors.neutral;
    }
    widget view = id.obj();
    view.set_default_var_range( u );
    const nc_color color = view.value_color( view.get_var_value( u ) );
    return color == c_unset ? colors.neutral : native_ink( color );
}

inline ink native_label_ink( const avatar &u, const char *name, color_status &colors )
{
    const widget_id id( name );
    if( !id.is_valid() ) {
        colors.complete = false;
        return colors.neutral;
    }
    widget view = id.obj();
    const styled_text text = native_styled_text( view.show( u, 80 ), colors.neutral );
    if( !text.valid ) {
        colors.complete = false;
        return colors.neutral;
    }
    // Keep the accepted full English name, using the first rendered native label
    // glyph's condition style, rather than substituting an HP-derived color.
    for( const color_run &run : text.runs ) {
        if( text.text.find_first_not_of( " \t\r\n", run.begin ) < run.end ) {
            return run.color;
        }
    }
    return colors.neutral;
}

inline color_status capture_native_colors( const avatar &u )
{
    color_status colors;
    colors.ready = true;
    colors.neutral = native_ink( c_light_gray );
    colors.track = native_ink( c_dark_gray ).foreground;
    colors.scalars.fill( colors.neutral );
    const char *const numbers[] = {
        "stamina_graph_classic",
        "hp_head_graph_no_label", "hp_torso_graph_no_label",
        "hp_left_arm_graph_no_label", "hp_right_arm_graph_no_label",
        "hp_left_leg_graph_no_label", "hp_right_leg_graph_no_label"
    };
    for( std::size_t i = 0; i < 7; ++i ) {
        colors.scalars[i] = native_number_ink( u, numbers[i], colors );
    }
    const char *const labels[] = {
        "bodypart_head_status_text", "bodypart_torso_status_text",
        "bodypart_larm_status_text", "bodypart_rarm_status_text",
        "bodypart_lleg_status_text", "bodypart_rleg_status_text"
    };
    const char *const stats[] = {"str_num", "dex_num", "int_num", "per_num", "speed_num", "focus_num"};
    for( std::size_t i = 0; i < 6; ++i ) {
        colors.scalars[7 + i] = native_label_ink( u, labels[i], colors );
        colors.scalars[13 + i] = native_number_ink( u, stats[i], colors );
    }
    colors.scalars[19] = native_label_ink( u, "move_mode_letter", colors );
    return colors;
}
} // namespace ds_hud
#endif
