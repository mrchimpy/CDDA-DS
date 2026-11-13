#include "ds_hud.h"

#include <chrono>
#include <mutex>
#include <limits>

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

void publish( int current, int maximum, const body_health &health, const core_status &core )
{
    const std::lock_guard<std::mutex> lock( mailbox_mutex );
    if( !mailbox.active ) {
        return; // Ignore menu previews, character creation, and stale redraws.
    }
    mailbox.ready = maximum > 0 && current >= 0;
    mailbox.current = mailbox.ready ? current : 0;
    mailbox.maximum = mailbox.ready ? maximum : 0;
    mailbox.health = mailbox.ready ? health : body_health{};
    mailbox.core = mailbox.ready ? core : core_status{};
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
std::array<std::int64_t, wire_field_count> wire_values( const snapshot &state )
{
    std::array<std::int64_t, wire_field_count> values = {
        state.active, state.ready, state.current, state.maximum,
        static_cast<std::int64_t>( state.sequence ), state.age_ms
    };
    for( int i = 0; i < 6; ++i ) {
        values[6 + i * 2] = state.health.current[i];
        values[7 + i * 2] = state.health.maximum[i];
    }
    values[18] = state.core.strength;
    values[19] = state.core.dexterity;
    values[20] = state.core.intelligence;
    values[21] = state.core.perception;
    values[22] = state.core.speed;
    values[23] = state.core.focus;
    return values;
}
} // namespace ds_hud

#if defined(__ANDROID__)
extern "C" JNIEXPORT jobjectArray JNICALL
Java_com_cleverraven_cataclysmdda_DualScreenHud_nativeSnapshot( JNIEnv *env, jclass )
{
    // One read under the mutex, including the string. No game objects on this thread.
    // Object[] { long[24], byte[] UTF-8 } avoids NewStringUTF's modified-UTF-8 rules.
    try {
        const ds_hud::snapshot state = ds_hud::read();
        const auto packed = ds_hud::wire_values( state );
        jlong values[ds_hud::wire_field_count];
        for( std::size_t i = 0; i < packed.size(); ++i ) {
            values[i] = static_cast<jlong>( packed[i] );
        }
        const std::string &name = state.core.movement_mode;
        if( name.size() > static_cast<std::size_t>( std::numeric_limits<jsize>::max() ) ) {
            return nullptr;
        }
        jclass object_class = env->FindClass( "java/lang/Object" );
        if( object_class == nullptr ) {
            return nullptr;
        }
        jobjectArray result = env->NewObjectArray( 2, object_class, nullptr );
        env->DeleteLocalRef( object_class );
        if( result == nullptr ) {
            return nullptr;
        }
        jlongArray numbers = env->NewLongArray( ds_hud::wire_field_count );
        if( numbers == nullptr ) {
            return nullptr;
        }
        env->SetLongArrayRegion( numbers, 0, ds_hud::wire_field_count, values );
        if( env->ExceptionCheck() ) {
            return nullptr;
        }
        jbyteArray movement = env->NewByteArray( static_cast<jsize>( name.size() ) );
        if( movement == nullptr ) {
            return nullptr;
        }
        if( !name.empty() ) {
            env->SetByteArrayRegion( movement, 0, static_cast<jsize>( name.size() ),
                                     reinterpret_cast<const jbyte *>( name.data() ) );
            if( env->ExceptionCheck() ) {
                return nullptr;
            }
        }
        env->SetObjectArrayElement( result, 0, numbers );
        if( env->ExceptionCheck() ) {
            return nullptr;
        }
        env->SetObjectArrayElement( result, 1, movement );
        if( env->ExceptionCheck() ) {
            return nullptr;
        }
        env->DeleteLocalRef( numbers );
        env->DeleteLocalRef( movement );
        return result;
    } catch( ... ) {
        // Never let a native allocation/copy exception cross the JNI boundary.
        return nullptr;
    }
}
#endif
