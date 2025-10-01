import { useState } from "react";

export default function Home() {
  const [name, setName] = useState("");
  const [origin, setOrigin] = useState("");
  const [preferences, setPreferences] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(
        process.env.NEXT_PUBLIC_API_URL + "/plan-trip",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_name: name,
            origin_city: origin,
            preferences: preferences,
          }),
        }
      );
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Error fetching trip plan");
    }
    setLoading(false);
  }

  return (
    <div className="flex flex-col items-center p-8 font-sans">
      <h1 className="text-3xl font-bold mb-4">🌍 AI Travel Planner</h1>

      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-3">
        <input
          className="w-full border rounded p-2"
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="w-full border rounded p-2"
          placeholder="Origin city"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          required
        />
        <textarea
          className="w-full border rounded p-2"
          placeholder="Travel preferences (e.g. rainy city trip in Europe)"
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          required
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded"
          disabled={loading}
        >
          {loading ? "Planning..." : "Plan my trip"}
        </button>
      </form>

      {result && (
        <div className="mt-6 w-full max-w-lg border rounded p-4 bg-gray-50">
          <h2 className="text-xl font-semibold mb-2">✈️ Trip Plan</h2>
          <p><strong>Destination:</strong> {result.destination}</p>
          <p><strong>Flight:</strong> {result.from_city} → {result.destination}, arriving {result.arrival_time}</p>
          <p><strong>Hotel:</strong> {result.hotel_name} ({result.hotel_location})</p>
          <h3 className="text-lg mt-3">🎯 Activities:</h3>
          <ul className="list-disc list-inside">
            {result.activities?.map((a: string, i: number) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
