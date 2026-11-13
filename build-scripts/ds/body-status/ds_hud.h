#ifndef CATA_SRC_DS_HUD_H
#define CATA_SRC_DS_HUD_H

#include <cstdint>
#include <array>

// One-way, copied state only. The Android UI must never access game objects.
namespace ds_hud
{
struct body_health {
    std::array<int, 6> current{};
    std::array<int, 6> maximum{};
};
struct snapshot {
    body_health health;
    bool active = false;
    bool ready = false;
    int current = 0;
    int maximum = 0;
    std::uint64_t sequence = 0;
    std::int64_t age_ms = 0;
};
void begin_session();
void end_session();
void publish( int current, int maximum, const body_health &health = {} );
snapshot read();

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
