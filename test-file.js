// Test file for VS Code extension
function testFunction() {
    console.log("This is a test function");
    
    // Some potential issues for review
    var unusedVariable = "test";
    let x = 1;
    let y = 2;
    
    if (x = y) { // Assignment instead of comparison
        console.log("This might be a bug");
    }
    
    return x + y;
}

// Call the function
testFunction();