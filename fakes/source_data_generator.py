import pyodbc
import random
from faker import Faker

'''
This code is to insert production data into MovieReviews database.
'''

#---------- CONFIG ----------
SERVER = 'vm-synthetic-da\\SQLEXPRESS'  # Change if needed
DATABASE = 'MovieReviews'
USERNAME = 'sa'  # Leave blank for Windows Authentication
PASSWORD = 'Jigzaz$1234567'  # Leave blank for Windows Authentication
USE_WINDOWS_AUTH = True

#---------- CONNECTION ----------
if USE_WINDOWS_AUTH:
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
else:
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
fake = Faker()

#---------- GENRE LIST ----------
real_genres = [
    "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Sport", "Thriller",
    "War", "Western"
]

#---------- CLEANUP ----------
cursor.execute("DELETE FROM Reviews")
cursor.execute("DELETE FROM Movies")
cursor.execute("DELETE FROM Genres")
conn.commit()

#---------- 1. Insert Genres ----------
for g in real_genres:
    cursor.execute("INSERT INTO Genres (GenreName) VALUES (?)", g)
conn.commit()

#Get Genre IDs mapping
cursor.execute("SELECT GenreID, GenreName FROM Genres ORDER BY GenreID")
genres_info = cursor.fetchall()
genre_id_map = {row[0]: row[1] for row in genres_info}

# ---------- 2. Genre Distribution Setup ----------
total_movies = 1000
top_3_genres = random.sample(list(genre_id_map.keys()), 3)
no_movie_genres = random.sample(
    [g for g in genre_id_map.keys() if g not in top_3_genres], 2
)
remaining_genres = [g for g in genre_id_map.keys() if g not in top_3_genres + no_movie_genres]

movies_in_top3 = int(total_movies * 0.60)
movies_in_remaining_genres = total_movies - movies_in_top3

print("\n--- Genre Distribution ---")
print("Top 3 genres (60% of movies):", [genre_id_map[g] for g in top_3_genres])
print("No movie genres:", [genre_id_map[g] for g in no_movie_genres])
print("Other genres (share remaining movies):", [genre_id_map[g] for g in remaining_genres])
print("---------------------------\n")

# ---------- 3. Insert Movies ----------
movies = []

# Movies for top 3 genres
for _ in range(movies_in_top3):
    genre = random.choice(top_3_genres)
    title = fake.sentence(nb_words=3).replace('.', '')
    release_year = random.randint(1980, 2024)
    duration = random.randint(80, 180)
    movies.append((title, release_year, duration, genre))

# Movies for remaining genres
while movies_in_remaining_genres > 0:
    genre = random.choice(remaining_genres)
    title = fake.sentence(nb_words=3).replace('.', '')
    release_year = random.randint(1980, 2024)
    duration = random.randint(80, 180)
    movies.append((title, release_year, duration, genre))
    movies_in_remaining_genres -= 1

cursor.executemany(
    "INSERT INTO Movies (Title, ReleaseYear, DurationMinutes, GenreID) VALUES (?, ?, ?, ?)",
    movies
)
conn.commit()

# Get Movie IDs
cursor.execute("SELECT MovieID FROM Movies ORDER BY MovieID")
movie_ids = [row[0] for row in cursor.fetchall()]

# ---------- 4. Insert Reviews ----------
total_reviews = 10000
no_review_movies = random.sample(movie_ids, 500)
movies_with_reviews = [m for m in movie_ids if m not in no_review_movies]

top_100_movies = random.sample(movies_with_reviews, 100)
remaining_movies = [m for m in movies_with_reviews if m not in top_100_movies]

reviews_for_top_100 = int(total_reviews * 0.90)  # 9000
reviews_for_remaining_400 = total_reviews - reviews_for_top_100  # 1000

reviews = []

# Reviews for top 100 movies
for _ in range(reviews_for_top_100):
    movie_id = random.choice(top_100_movies)
    reviewer = fake.first_name()
    rating = random.randint(1, 10)
    review_text = fake.sentence(nb_words=12)
    review_date = fake.date_between(start_date='-5y', end_date='today')
    reviews.append((movie_id, reviewer, rating, review_text, review_date))

# Reviews for remaining 400 movies
for _ in range(reviews_for_remaining_400):
    movie_id = random.choice(remaining_movies)
    reviewer = fake.first_name()
    rating = random.randint(1, 10)
    review_text = fake.sentence(nb_words=12)
    review_date = fake.date_between(start_date='-5y', end_date='today')
    reviews.append((movie_id, reviewer, rating, review_text, review_date))

cursor.executemany(
    "INSERT INTO Reviews (MovieID, ReviewerName, Rating, ReviewText, ReviewDate) VALUES (?, ?, ?, ?, ?)",
    reviews
)
conn.commit()

print("✅ Data generation completed successfully.")

cursor.close()
conn.close()
