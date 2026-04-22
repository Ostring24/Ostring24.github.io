# How The Heck Does GPS Work? (An Interactive Exploration)

# How The Heck Does GPS Work?

How geometry, stopwatches, and Einstein's theories work together to make GPS possible.

![Shri Khalpada](https://perthirtysix.com/people/shri-bw.jpg)

Shri Khalpada

April 11, 2026

Part of *How The Heck?*, a series of interactive explanations of everyday technology.

[1QR CodesBlack-and-white squares that survive coffee stains](https://perthirtysix.com/how-the-heck-do-qr-codes-work)[2GPSTurning time into distance with Einstein's help](https://perthirtysix.com/how-the-heck-does-gps-work)[3ShazamA connect-the-dots trick for sound](https://perthirtysix.com/how-the-heck-does-shazam-work)

If you like these, you can follow the [author](https://bsky.app/profile/shrikhalpada.dev) or buy him a [coffee](https://www.buymeacoffee.com/shrikhalpada)!

If you're like me, you might be entirely dependent on GPS to navigate the world. At some point, you may have caught yourself wondering during those panicked moments when an exit is coming up and your phone is recalibrating: how does my phone even know where I am?

The answer is in some ways simpler than you'd expect, and in other ways more complex. GPS is fundamentally a translation tool: it converts time into distance. A satellite sends a signal, your phone catches it, and the delay between those two events tells the phone exactly how far away the satellite is. Everything else is about making that measurement precise enough to be useful: accounting for bad clocks, satellite geometry, and eventually, Einstein's theories.

### The Ruler

TL;DR

GPS turns time into distance. 1 nanosecond of signal travel = 0.3 meters.

Every GPS measurement starts with a stopwatch. A satellite broadcasts a signal at the speed of light. Your phone receives it and checks how long the trip took. Multiply the travel time by the speed of light, and you get the distance.

Send Signal

This is the fundamental building block of GPS.

### One Satellite, One Ring

TL;DR

One satellite tells you how far away you are, but not which direction. You could be anywhere on a ring.

Measuring a single satellite gives you a distance, but not a direction. If a signal takes  to reach your phone, you are roughly  from the satellite. If you took every point at that distance from the satellite, you would get a ring on the surface of the Earth (technically an oblate spheroid, but effectively a ring for our purposes). One satellite tells us we're somewhere on that ring, but it can't tell us where exactly.

Why a ring? What about altitude?

To visualize where you might be on Earth's surface, think of two soap bubbles touching. Where they overlap, they share a perfect circle. The satellite's signal is one sphere, and the Earth is the other. Where they intersect, you get a ring on the surface. You are somewhere on this ring, because every point on it is the same distance from the satellite.

This is a useful mental model, but GPS does not actually use the Earth's surface as a constraint. It solves for a full 3D position, including altitude, which is how it works for aircraft and spacecraft too. We project the result onto the globe here for clarity, but the real math operates in open 3D space.

Not to scale

Satellite A sends a signal to your phone at the speed of light.

Ping Satellite A  Reset

Try pinging the satellite to see its signal reach Earth.

### Three Satellites, One Point

TL;DR

Three satellites produce three rings that intersect at a single point: your location.

One ring isn't enough since you could be anywhere along it. A second satellite produces a second ring which crosses the first one at exactly two points. A third satellite produces a third ring, which passes through only one of those two points.

This process is called trilateration. Each satellite gives you one equation:

is the known position of satellite , and  is the measured distance. We can solve for three unknowns  with three equations.

Not to scale

Each satellite's ring passes through your location.

Ping A  Ping B  Ping C  Reset

Try pinging the satellites one at a time.

Don't three spheres give two points, not one?

Technically, yes. Two spheres intersect to form a circle. The third sphere cuts through that circle at two points. But one of those two points is almost always an unusable location, either deep inside the Earth or thousands of kilometers out in space. The receiver discards it. So in practice, three satellites resolve to a single point on the surface.

### The Clock Problem

TL;DR

Your phone's clock is (relatively) bad. A 4th satellite fixes it because with four satellites, there is only one clock correction that makes all four spheres intersect at a single point.

There's a problem with the math above: it assumes your phone knows the travel time  perfectly.

Each GPS satellite carries an incredibly precise atomic clock, accurate to about . Your phone has a much cheaper quartz crystal oscillator that can naturally drift by microseconds (thousands of nanoseconds). Since  of clock error produces  of position error, even  of drift puts you  off. Without accounting for this, GPS would become pretty useless pretty quickly!

The fix is to add another satellite.

In simple terms: there is only one specific clock correction possible where all four spheres intersect at a single, perfect point. The 4th satellite gives the receiver enough information to find it. Once it does, it corrects every distance measurement at once, and the previously fuzzy answer snaps into focus. Conceptually, you can think about the system doing some math to figure out how to make the new red ring below perfectly intersect with the other three rings.

The math behind clock correction

Your phone's clock error () becomes a 4th unknown:

The left side is the true geometric distance to satellite .  is the pseudorange, the distance your phone measured using its imperfect clock. It's called "pseudo" because it's wrong by the same constant offset for every satellite.  is that offset, converted from time into meters. The same  appears in all four equations because the phone has one clock, and it's off by one amount.

The receiver linearizes this system and iterates toward a solution for all four unknowns  simultaneously. When it converges, the four spheres meet at a single point. At that moment, the receiver has found both its position and the true time.

Not to scale

Phone Clock Error

Add 4th Satellite Reset

This is also why your phone's clock is so accurate. It's constantly being synced to atomic clocks in space!

### The Relativity Tax

TL;DR

Without Einstein's corrections, GPS drifts by ~10 km per day.

Even with four satellites and a solved clock, we're not quite done yet.

To understand why, we have to think of time itself as a clock that can be sped up or slowed down by its surroundings. GPS has to account for two specific distortions:

* Special Relativity (speed): Einstein discovered that the faster an object moves, the slower time passes for it. GPS satellites move at roughly , so their clocks lose about  per day compared to ours.
* General Relativity (gravity): Gravity also warps time. The further you are from a massive object like Earth, the faster time ticks. The satellites orbit at  altitude in weaker gravity, so their clocks gain about  per day.

These two effects don't cancel out. The gravity gain is much stronger than the speed loss.

Without a correction, the satellite clocks would run  ahead of ground clocks every day. Because light travels  every microsecond, that small offset would cause your position to drift by roughly  every 24 hours.

Engineers bake this correction into the hardware. The satellite clocks are built to tick slightly too slow on the ground, at  instead of the nominal . Once in orbit, the combination of weaker gravity and orbital speed makes them tick at exactly the correct rate.

Not to scale

Elapsed Time Without Correction

Day 0: drift = 0 μs≈ 0 km error

Apply Relativity Corrections Reset

Without these corrections, GPS would become unusable within hours. The fact that your phone can pinpoint your location to within a few meters is, in addition to being a modern miracle, a quiet and continuous proof that Einstein was right.

### A Joint Effort

In practice, your phone doesn't stop at four satellites. Modern receivers typically lock onto 8 to 12 at once, sometimes more. The extra signals don't change the core math, but they let the receiver average out errors and pick the best satellite geometry. More satellites means sharper intersections and a more stable fix.

And it's not just the American GPS constellation. Russia operates GLONASS, the EU has Galileo, and China has BeiDou. Your phone can listen to all of them simultaneously. That means over 100 atomic stopwatches orbiting overhead, built by different countries, all working together to tell you where you are.

Satellite placement also matters. If the satellites are clumped together in one part of the sky, their rings intersect at very shallow angles. This creates a wide, blurry area of uncertainty around the true position. GPS engineers call this Geometric Dilution of Precision (GDOP). Good geometry means satellites spread across the sky, so that their rings cross at sharp angles and produce a tight, high-confidence intersection point. Your phone's GPS chip automatically selects the best combination of visible satellites to minimize GDOP.

In cities, GPS signals can bounce off buildings before reaching your phone. This makes the stopwatch think you are further away than you actually are, because the signal took a longer path. This is called multipath error, and it's the main reason GPS gets less accurate in dense urban areas. Modern receivers use multiple techniques to detect and filter out these reflected signals, but it remains one of the hardest problems in GPS.

With all that said, I find it amazing that your phone can pinpoint your location to within a few meters using nothing more than the time it takes light to travel from a few satellites tens of thousands of kilometers away.

If you want to go much deeper, Bartosz Ciechanowski's [interactive explainer on GPS](https://ciechanow.ski/gps/) is the gold standard. It covers signal modulation, orbital mechanics, and receiver architecture in far more detail than we do here.

### Thank you!

If you like this type of content, you can follow me on [BlueSky](https://bsky.app/profile/shrikhalpada.dev). If you wanted to support me further, buying me a  [coffee](https://www.buymeacoffee.com/shrikhalpada) would be much appreciated. It helps us keep the lights on and the servers running! ☕

We're just getting started.

Subscribe for more thoughtful, data-driven explorations.