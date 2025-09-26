#!/usr/bin/env python3
"""
Test script for downtown mapping and distance calculation logic

This script tests the new downtown service to ensure:
1. Different properties get different downtown mappings
2. Local downtown is preferred when available
3. Fallback to major downtowns works correctly
4. Distance calculations are accurate and unique per property
5. Labels are clear (e.g., "Dallas Downtown", "Denton Downtown")
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.downtown_service import downtown_service


async def test_downtown_logic():
    """Test the downtown mapping logic with various scenarios"""

    print("🧪 Testing Downtown Mapping Logic")
    print("=" * 50)

    # Test cases: Different properties in Texas
    test_properties = [
        {
            'name': 'Denton Property',
            'city': 'Denton',
            'state': 'TX',
            'coords': (33.2148, -97.1331)  # Denton, TX coordinates
        },
        {
            'name': 'Dallas Property',
            'city': 'Dallas',
            'state': 'TX',
            'coords': (32.7767, -96.7970)  # Dallas, TX coordinates
        },
        {
            'name': 'Plano Property',
            'city': 'Plano',
            'state': 'TX',
            'coords': (33.0198, -96.6989)  # Plano, TX coordinates
        },
        {
            'name': 'Small Town Property',
            'city': 'Celina',
            'state': 'TX',
            'coords': (33.3248, -96.7847)  # Celina, TX coordinates
        }
    ]

    results = []

    for prop in test_properties:
        print(f"\n🏠 Testing: {prop['name']} ({prop['city']}, {prop['state']})")
        print("-" * 40)

        try:
            # Find appropriate downtown
            downtown_label, downtown_coords = await downtown_service.find_appropriate_downtown(
                prop['city'], prop['state'], prop['coords'][0], prop['coords'][1]
            )

            # Get commute time
            commute_time = await downtown_service.get_commute_time_to_downtown(
                prop['coords'][0], prop['coords'][1], downtown_label, downtown_coords
            )

            result = {
                'property': prop['name'],
                'downtown_label': downtown_label,
                'downtown_coords': downtown_coords,
                'commute_time': commute_time
            }
            results.append(result)

            print(f"  🏙️ Downtown: {downtown_label}")
            if downtown_coords:
                print(f"  📍 Coordinates: {downtown_coords}")
            print(f"  🚗 Commute: {commute_time}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'property': prop['name'],
                'error': str(e)
            })

    # Analysis
    print("\n" + "=" * 50)
    print("📊 ANALYSIS")
    print("=" * 50)

    # Check for unique downtowns
    downtown_labels = [r.get('downtown_label') for r in results if 'downtown_label' in r]
    unique_labels = set(downtown_labels)

    print(f"✅ Found {len(unique_labels)} unique downtown destinations:")
    for label in unique_labels:
        count = downtown_labels.count(label)
        print(f"  - {label}: {count} property/properties")

    # Check for proper labeling
    print(f"\n✅ Downtown labeling analysis:")
    properly_labeled = 0
    for label in unique_labels:
        if 'Downtown' in label and len(label.split()) >= 2:
            properly_labeled += 1
            print(f"  ✓ {label} - Properly labeled")
        else:
            print(f"  ⚠️ {label} - Could be clearer")

    print(f"\n✅ {properly_labeled}/{len(unique_labels)} downtown labels are properly formatted")

    # Check for different commute times
    commute_times = [r.get('commute_time') for r in results if 'commute_time' in r and r.get('commute_time')]
    unique_times = set(commute_times)

    print(f"\n✅ Found {len(unique_times)} unique commute times:")
    for time in unique_times:
        count = commute_times.count(time)
        print(f"  - {time}: {count} property/properties")

    if len(unique_times) > 1:
        print("  ✅ SUCCESS: Different properties have different commute times!")
    else:
        print("  ⚠️ WARNING: All properties have the same commute time")

    return results


async def test_fallback_scenarios():
    """Test fallback scenarios"""

    print("\n\n🧪 Testing Fallback Scenarios")
    print("=" * 50)

    # Test properties in different states
    fallback_tests = [
        {'city': 'Princeton', 'state': 'NJ', 'coords': (40.3573, -74.6672)},
        {'city': 'San Jose', 'state': 'CA', 'coords': (37.3382, -121.8863)},
        {'city': 'Unknown City', 'state': 'ZZ', 'coords': (40.0, -100.0)}
    ]

    for prop in fallback_tests:
        print(f"\n🏠 Testing: {prop['city']}, {prop['state']}")
        print("-" * 30)

        try:
            downtown_label, downtown_coords = await downtown_service.find_appropriate_downtown(
                prop['city'], prop['state'], prop['coords'][0], prop['coords'][1]
            )

            print(f"  🏙️ Downtown: {downtown_label}")
            if downtown_coords:
                print(f"  📍 Coordinates: {downtown_coords}")
            else:
                print(f"  📍 Coordinates: Not available")

        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    async def main():
        print("🚀 Starting Downtown Logic Test\n")

        # Test main logic
        results = await test_downtown_logic()

        # Test fallback scenarios
        await test_fallback_scenarios()

        print("\n" + "=" * 50)
        print("🎉 Test Complete!")
        print("=" * 50)

    asyncio.run(main())