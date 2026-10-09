export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const apiKey = process.env.ANAKIN_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const { location, track, subject } = req.body || {};
    
    if (!location || !track || !subject) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const prompt = `Find ${track} and NEET educators, teachers, faculties, mentors, and content creators in ${location} who teach ${subject} for ${track} preparation. Look for publicly available profiles and evidence from platforms such as Instagram, YouTube, LinkedIn, Reddit, Facebook and other public websites. Prioritize actual educators rather than coaching institutes, generic education pages, student profiles, or unrelated people. Return useful public profile URLs and snippets when available.`;

    const response = await fetch('https://api.anakin.io/v1/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
      // Do not expose API key or internal anakin errors
      return res.status(502).json({ error: 'Failed to fetch from search provider' });
    }

    const data = await response.json();
    const rawResults = data.results || [];

    // Map raw Anakin search results to the frontend's expected Educator structure
    const frontendResults = rawResults.map((item, index) => {
      // Basic extraction from title (e.g., "Alakh Pandey - Physics Wallah | LinkedIn")
      let name = item.title || "Unknown Educator";
      if (name.includes(' - ')) name = name.split(' - ')[0];
      if (name.includes(' | ')) name = name.split(' | ')[0];
      
      const url = item.url || "";
      let platform = "Other";
      if (url.includes('instagram.com')) platform = "Instagram";
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = "YouTube";
      else if (url.includes('linkedin.com')) platform = "LinkedIn";
      else if (url.includes('facebook.com')) platform = "Facebook";

      return {
        educator_id: `temp-${index}`,
        name: name.trim(),
        location: location,
        track: track,
        subjects: [subject],
        scores: {
          overall: 85,
          reasons: [item.snippet || "Found via Anakin search"]
        },
        profiles: [
          {
            platform: platform,
            url: url,
            followers: 0
          }
        ]
      };
    });

    return res.status(200).json({ 
      results: frontendResults, 
      last_updated: new Date().toISOString() 
    });

  } catch (error) {
    // Log the actual error on the server but return a generic message to the client
    console.error('Search API Error:', error);
    return res.status(500).json({ error: 'Internal server error during search' });
  }
}
