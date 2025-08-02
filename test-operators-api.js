// Test operators API endpoint
async function testOperatorsAPI() {
  const url = 'https://tiny-tapioca-72f6c6.netlify.app/api/operators';
  
  try {
    console.log('Testing operators API at:', url);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    const data = await response.text();
    console.log('Response data:', data);
    
    if (response.ok) {
      console.log('✅ Operators API is working!');
      try {
        const json = JSON.parse(data);
        console.log('Number of operators:', json.length);
      } catch (e) {
        console.log('Response is not JSON:', e.message);
      }
    } else {
      console.log('❌ Operators API returned error');
    }
  } catch (error) {
    console.error('❌ Failed to connect to API:', error.message);
  }
}

// Run the test
testOperatorsAPI();