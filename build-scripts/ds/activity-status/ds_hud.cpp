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

void publish( int current, int maximum, const body_health &health, const core_status &core,
              const activity_status &activity )
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
    mailbox.activity = mailbox.ready ? activity : activity_status{};
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
    for( std::size_t i = 0; i < activity_field_count; ++i ) {
        values[24 + i] = state.activity.available[i];
    }
    return values;
}
} // namespace ds_hud

#if defined(__ANDROID__)
extern "C" JNIEXPORT jobjectArray JNICALL
Java_com_cleverraven_cataclysmdda_DualScreenHud_nativeSnapshot( JNIEnv *env, jclass )
{
    // Object[] { long[29], byte[6][] }, all from one locked mailbox copy.
    // Plain UTF-8 bytes avoid NewStringUTF's modified-UTF-8 requirements.
    try {
        const ds_hud::snapshot state = ds_hud::read();
        const auto packed = ds_hud::wire_values( state );
        jlong values[ds_hud::wire_field_count];
        for( std::size_t i = 0; i < packed.size(); ++i ) {
            values[i] = static_cast<jlong>( packed[i] );
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
        env->SetObjectArrayElement( result, 0, numbers );
        env->DeleteLocalRef( numbers );
        if( env->ExceptionCheck() ) {
            return nullptr;
        }
        jclass bytes_class = env->FindClass( "[B" );
        if( bytes_class == nullptr ) {
            return nullptr;
        }
        jobjectArray texts = env->NewObjectArray( 1 + ds_hud::activity_field_count,
                             bytes_class, nullptr );
        env->DeleteLocalRef( bytes_class );
        if( texts == nullptr ) {
            return nullptr;
        }
        for( std::size_t i = 0; i <= ds_hud::activity_field_count; ++i ) {
            const std::string &text = i == 0 ? state.core.movement_mode : state.activity.text[i - 1];
            if( text.size() > static_cast<std::size_t>( std::numeric_limits<jsize>::max() ) ) {
                return nullptr;
            }
            jbyteArray bytes = env->NewByteArray( static_cast<jsize>( text.size() ) );
            if( bytes == nullptr ) {
                return nullptr;
            }
            if( !text.empty() ) {
                env->SetByteArrayRegion( bytes, 0, static_cast<jsize>( text.size() ),
                                         reinterpret_cast<const jbyte *>( text.data() ) );
                if( env->ExceptionCheck() ) {
                    return nullptr;
                }
            }
            env->SetObjectArrayElement( texts, static_cast<jsize>( i ), bytes );
            env->DeleteLocalRef( bytes );
            if( env->ExceptionCheck() ) {
                return nullptr;
            }
        }
        env->SetObjectArrayElement( result, 1, texts );
        env->DeleteLocalRef( texts );
        if( env->ExceptionCheck() ) {
            return nullptr;
        }
        return result;
    } catch( ... ) {
        // Allocation/copy failures must never unwind across JNI.
        return nullptr;
    }
}
#endif
