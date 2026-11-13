#ifndef CATA_SRC_DS_HUD_H
#define CATA_SRC_DS_HUD_H

#include <cstdint>
#include <array>
#include <string>

// One-way, copied state only. The Android UI must never access game objects.
namespace ds_hud
{
struct body_health {
    std::array<int, 6> current{};
    std::array<int, 6> maximum{};
};
struct core_status {
    int strength = 0;
    int dexterity = 0;
    int intelligence = 0;
    int perception = 0;
    int speed = 0;
    int focus = 0;
    // Copied UTF-8 game-provided name and sidebar letter; never a game pointer.
    std::string movement_mode;
};
struct snapshot {
    body_health health;
    core_status core;
    bool active = false;
    bool ready = false;
    int current = 0;
    int maximum = 0;
    std::uint64_t sequence = 0;
    std::int64_t age_ms = 0;
};
void begin_session();
void end_session();
void publish( int current, int maximum, const body_health &health = {},
              const core_status &core = {} );
snapshot read();

// JNI numeric payload: original 18 fields, then STR, DEX, INT, PER, speed, focus.
// Movement text travels as UTF-8 bytes in the same JNI result, from this same copy.
constexpr std::size_t wire_field_count = 24;
std::array<std::int64_t, wire_field_count> wire_values( const snapshot &state );

// Construct only after opening_screen() has entered a real game. This also
// clears the mailbox when the loop exits via an exception or normal save/quit.
class session_scope
{
    public:
        session_scope() { begin_session(); }
        ~session_scope() { end_session(); }
        session_scope( const session_scope & ) = delete;
        session_scope &operator=( const session_scope & ) = delete;
};
} // namespace ds_hud
#endif
