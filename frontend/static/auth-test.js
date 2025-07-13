/**
 * Test script to diagnose authentication flow issues
 * Run this in browser console to test the auth flow
 */

// Test 1: Check API connectivity
async function testBackendConnectivity() {
    console.log('🔍 Testing backend connectivity...');
    
    try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        console.log('✅ Backend health:', data);
        return true;
    } catch (error) {
        console.error('❌ Backend not accessible:', error);
        return false;
    }
}

// Test 2: Check login endpoint
async function testLoginEndpoint() {
    console.log('🔍 Testing login endpoint...');
    
    try {
        const response = await fetch('http://localhost:8000/auth/login', {
            method: 'GET',
            redirect: 'manual'
        });
        
        console.log('Login endpoint status:', response.status);
        if (response.status === 302) {
            const location = response.headers.get('Location');
            console.log('✅ Redirects to:', location?.substring(0, 100) + '...');
            return location?.includes('login.microsoftonline.com') || false;
        } else {
            console.log('❌ Unexpected status:', response.status);
            return false;
        }
    } catch (error) {
        console.error('❌ Login endpoint error:', error);
        return false;
    }
}

// Test 3: Check user endpoint (should be 401)
async function testUserEndpoint() {
    console.log('🔍 Testing user endpoint...');
    
    try {
        const response = await fetch('http://localhost:8000/auth/user', {
            credentials: 'include'
        });
        
        console.log('User endpoint status:', response.status);
        if (response.status === 401) {
            console.log('✅ User endpoint correctly requires authentication');
            return true;
        } else {
            console.log('❌ Unexpected status:', response.status);
            const text = await response.text();
            console.log('Response:', text);
            return false;
        }
    } catch (error) {
        console.error('❌ User endpoint error:', error);
        return false;
    }
}

// Test 4: Check cookies
function testCookies() {
    console.log('🔍 Checking current cookies...');
    
    const cookies = document.cookie;
    console.log('Current cookies:', cookies || 'None');
    
    const authCookies = ['access_token', 'refresh_token', 'auth_session'];
    const foundCookies = authCookies.filter(name => 
        cookies.includes(`${name}=`)
    );
    
    if (foundCookies.length > 0) {
        console.log('✅ Found auth cookies:', foundCookies);
        return true;
    } else {
        console.log('ℹ️ No auth cookies found (expected if not logged in)');
        return false;
    }
}

// Test 5: Manual login redirect
function testManualLogin() {
    console.log('🔍 Testing manual login redirect...');
    console.log('This will redirect to the login endpoint...');
    
    setTimeout(() => {
        window.location.href = 'http://localhost:8000/auth/login';
    }, 2000);
}

// Run all tests
async function runAllTests() {
    console.log('🚀 Starting authentication flow diagnostics...\n');
    
    const results = {
        backend: await testBackendConnectivity(),
        login: await testLoginEndpoint(),
        user: await testUserEndpoint(),
        cookies: testCookies()
    };
    
    console.log('\n📋 Test Results:');
    console.log('Backend connectivity:', results.backend ? '✅' : '❌');
    console.log('Login endpoint:', results.login ? '✅' : '❌');
    console.log('User endpoint:', results.user ? '✅' : '❌');
    console.log('Auth cookies:', results.cookies ? '✅' : 'ℹ️');
    
    if (results.backend && results.login && results.user) {
        console.log('\n✅ Backend configuration appears correct');
        console.log('🔍 Try running testManualLogin() to test the full flow');
    } else {
        console.log('\n❌ Some tests failed - check backend configuration');
    }
    
    return results;
}

// Export functions for manual testing
window.authTest = {
    runAllTests,
    testBackendConnectivity,
    testLoginEndpoint,
    testUserEndpoint,
    testCookies,
    testManualLogin
};

console.log('Auth test utilities loaded. Run authTest.runAllTests() to start.');
