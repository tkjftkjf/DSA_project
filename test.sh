for f in dungeon_crawler/dungeon_crawler/templates/rooms/{start,normal,boss}/{0..5}.txt; do
    printf '00000\n00000\n00000\n00000\n00000\n' > "$f"
done