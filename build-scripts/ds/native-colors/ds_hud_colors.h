#ifndef CATA_SRC_DS_HUD_COLORS_H
#define CATA_SRC_DS_HUD_COLORS_H

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

// Portable copied presentation data. No game/Android pointers, palette lookups,
// thresholds or mutable game objects may cross the mailbox boundary.
namespace ds_hud
{
struct ink {
    std::uint32_t foreground = 0xff969696;
    std::uint32_t background = 0xff000000;
    bool operator==( const ink &other ) const {
        return foreground == other.foreground && background == other.background;
    }
};
struct color_run {
    std::size_t begin = 0;
    std::size_t end = 0;
    ink color;
};
constexpr std::size_t color_scalar_count = 20;
constexpr std::size_t color_widget_count = 29;
constexpr std::size_t color_text_limit = 65536;
constexpr std::size_t color_run_limit = 4096;
// Scalars: stamina, six HP bars, six body labels, six core numbers, movement.
struct color_status {
    bool ready = false;
    bool complete = true;
    ink neutral;
    std::uint32_t track = 0xff636363;
    std::array<ink, color_scalar_count> scalars{};
    std::array<std::vector<color_run>, color_widget_count> runs{};
};
struct styled_text {
    bool valid = true;
    std::string text;
    std::vector<color_run> runs;
};
struct parsed_tag {
    enum class kind { literal, open, close } type = kind::literal;
    ink color;
};

// Resolver delegates tag recognition and RGB resolution to the running game.
// Byte offsets deliberately remain UTF-8 until the Java boundary, not UTF-16.
template<typename Resolver>
styled_text parse_markup( std::string_view marked, ink neutral, Resolver resolve )
{
    styled_text result;
    if( marked.size() > color_text_limit ) {
        result.valid = false;
        return result;
    }
    std::vector<ink> stack( 1, neutral );
    auto append = [&]( std::string_view text ) {
        if( text.empty() ) {
            return;
        }
        const std::size_t start = result.text.size();
        result.text.append( text.data(), text.size() );
        if( !result.runs.empty() && result.runs.back().color == stack.back() ) {
            result.runs.back().end = result.text.size();
        } else {
            result.runs.push_back( {start, result.text.size(), stack.back()} );
        }
    };
    std::size_t pos = 0;
    while( pos < marked.size() ) {
        const std::size_t next = marked.find( '<', pos );
        if( next == std::string_view::npos ) {
            append( marked.substr( pos ) );
            break;
        }
        append( marked.substr( pos, next - pos ) );
        const std::size_t end = marked.find( '>', next );
        if( end == std::string_view::npos ) {
            append( marked.substr( next ) );
            break;
        }
        const std::string_view candidate = marked.substr( next, end - next + 1 );
        const parsed_tag tag = resolve( candidate );
        if( tag.type == parsed_tag::kind::open ) {
            stack.push_back( tag.color );
        } else if( tag.type == parsed_tag::kind::close ) {
            if( stack.size() > 1 ) {
                stack.pop_back();
            }
        } else {
            // Do not swallow a real color tag nested after a literal '<'.
            append( marked.substr( next, 1 ) );
            pos = next + 1;
            continue;
        }
        if( stack.size() > 256 || result.runs.size() > color_run_limit ) {
            result.valid = false;
            result.runs.clear();
            return result;
        }
        pos = end + 1;
    }
    if( result.runs.size() > color_run_limit ) {
        result.valid = false;
        result.runs.clear();
    }
    return result;
}

// DSC1 / version 1. Fixed integers, no pointer ABI or host-endian byte structures.
inline std::vector<std::int64_t> pack_colors( const color_status &colors,
        std::uint64_t sequence )
{
    std::vector<std::int64_t> out = {0x44534331, 1, static_cast<std::int64_t>( sequence ),
        colors.ready, colors.complete, colors.neutral.foreground,
        colors.neutral.background, colors.track, color_scalar_count};
    for( const ink &color : colors.scalars ) {
        out.push_back( color.foreground );
        out.push_back( color.background );
    }
    out.push_back( color_widget_count );
    for( const auto &runs : colors.runs ) {
        out.push_back( static_cast<std::int64_t>( runs.size() ) );
        for( const color_run &run : runs ) {
            out.push_back( static_cast<std::int64_t>( run.begin ) );
            out.push_back( static_cast<std::int64_t>( run.end ) );
            out.push_back( run.color.foreground );
            out.push_back( run.color.background );
        }
    }
    return out;
}
} // namespace ds_hud
#endif
