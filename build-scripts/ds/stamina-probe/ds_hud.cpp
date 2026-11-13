#include "ds_hud.h"

#include <chrono>
#include <mutex>

#if defined(__ANDROID__)
#include <jni.h>
#endif

namespace ds_hud
{
namespace
{
std::mutex mailbox_mutex;
snapshot mailbox;
std::chrono::steady_clock::time_point published_at;
}

void begin_session()
{
    const std::lock_guard<std::mutex> lock( mailbox_mutex );
    const auto sequence = mailbox.sequence + 1;
    mailbox = {};
    mailbox.active = true;
    mailbox.sequence = sequence;
}

void end_session()
{
    const std::lock_guard<std::mutex> lock( mailbox_mutex );
    const auto sequence = mailbox.sequence + 1;
    mailbox = {};
    mailbox.sequence = sequence;
}

void publish( int current, int maximum )
{
    const std::lock_guard<std::mutex> lock( mailbox_mutex );
    if( !mailbox.active ) {
        return; // Ignore menu previews, character creation, and stale redraws.
    }
    mailbox.ready = maximum > 0 && current >= 0;
    mailbox.current = mailbox.ready ? current : 0;
    mailbox.maximum = mailbox.ready ? maximum : 0;
    ++mailbox.sequence;
    published_at = std::chrono::steady_clock::now();
}

snapshot read()
{
    const std::lock_guard<std::mutex> lock( mailbox_mutex );
    snapshot result = mailbox;
    if( result.ready ) {
        result.age_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                            std::chrono::steady_clock::now() - published_at ).count();
    }
    return result;
}
} // namespace ds_hud

#if defined(__ANDROID__)
extern "C" JNIEXPORT jlongArray JNICALL
Java_com_cleverraven_cataclysmdda_DualScreenHud_nativeSnapshot( JNIEnv *env, jclass )
{
    // This reader may run on Android's UI thread: it touches the mailbox only.
    const ds_hud::snapshot state = ds_hud::read();
    const jlong values[] = { state.active, state.ready, state.current, state.maximum,
                            static_cast<jlong>( state.sequence ), state.age_ms };
    jlongArray result = env->NewLongArray( 6 );
    if( result != nullptr ) {
        env->SetLongArrayRegion( result, 0, 6, values );
    }
    return result;
}
#endif
