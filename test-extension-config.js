// Test file for Kiro IDE Extension
// Bu dosyayı kullanarak extension'ı test edebilirsin

console.log("🔧 Testing MCP Ecosystem Platform Extension");

function testFunction() {
    // Bu fonksiyon AI code review için test edilecek
    const data = {
        name: "test",
        value: 123
    };
    
    // Potential issue: missing error handling
    return data.nonExistentProperty.toString();
}

// Test different code patterns
class TestClass {
    constructor(name) {
        this.name = name;
    }
    
    // Missing return type annotation
    getName() {
        return this.name;
    }
}

// Async function without proper error handling
async function fetchData(url) {
    const response = await fetch(url);
    return response.json(); // No error handling
}

// Export for testing
module.exports = {
    testFunction,
    TestClass,
    fetchData
};