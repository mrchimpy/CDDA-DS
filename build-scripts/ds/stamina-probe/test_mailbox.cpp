#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <thread>

int main()
{
    using namespace ds_hud;
    assert( !read().active && !read().ready );
    publish( 100, 200 );
    assert( !read().ready );
    {
        const session_scope session;
        assert( read().active && !read().ready );
        publish( 50, 100 );
        const auto a = read();
        assert( a.ready && a.current == 50 && a.maximum == 100 && a.age_ms >= 0 );
        publish( 25, 100 );
        assert( read().current == 25 && read().sequence > a.sequence );
        publish( 1, 0 );
        assert( !read().ready && read().maximum == 0 );
        publish( -1, 100 );
        assert( !read().ready );
    }
    assert( !read().active && !read().ready && read().current == 0 );
    try {
        const session_scope session;
        publish( 1, 2 );
        throw 1;
    } catch( int ) {}
    assert( !read().active && !read().ready );
    {
        const session_scope session;
        std::atomic<bool> done{false};
        std::thread writer( [&] {
            for( int i = 1; i <= 10000; ++i ) publish( i, i * 2 );
            done = true;
        } );
        do {
            const auto value = read();
            assert( !value.ready || value.current * 2 == value.maximum );
        } while( !done );
        writer.join();
        assert( read().current == 10000 );
    }
    assert( !read().active );
}
