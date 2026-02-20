import pandas as pd
import argparse
import sys

class MovieDB:
    def __init__(self, csv_file='disney movie total gross.csv'): #disney db
        try:
            self.df = pd.read_csv(csv_file)
            # (DD/MM/YYYY format)
            self.df['Date Released'] = pd.to_datetime(self.df['Date Released'], format='%d/%m/%Y')
            # Add season (nums cooresposnd to month, obv sorted for seasons)
            self.df['Season'] = self.df['Date Released'].dt.month.map({
                12: 'Winter', 1: 'Winter', 2: 'Winter',
                3: 'Spring', 4: 'Spring', 5: 'Spring',
                6: 'Summer', 7: 'Summer', 8: 'Summer',
                9: 'Fall', 10: 'Fall', 11: 'Fall'
            })
            print(f"✅ Loaded {len(self.df)} movies", file=sys.stderr)
        except FileNotFoundError:
            print(f"error: {csv_file} not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"error loading data: {e}", file=sys.stderr)
            sys.exit(1)
    
    def filter(self, genre=None, season=None, year=None, year_start=None, year_end=None, 
            rating=None, min_gross=None):
        """Apply filters to the database"""
        result = self.df.copy()
        
        if genre:
            result = result[result['Genre'].str.contains(genre, case=False, na=False)]
        if season:
            result = result[result['Season'] == season]
        if year:
            result = result[result['Date Released'].dt.year == year]
        if year_start and year_end:
            result = result[result['Date Released'].dt.year.between(year_start, year_end)]
        if rating:
            result = result[result['MPAA Rating'] == rating.upper()]
        if min_gross:
            result = result[result['Total Gross'] >= float(min_gross) * 1_000_000]
        
        return result
    
    def sort(self, data, sort_by='gross', ascending=False):
        """Sort the filtered data"""
        sort_columns = {
            'gross': 'Total Gross',
            'inflation': 'Inflation Adjusted Gross',
            'date': 'Date Released',
            'title': 'Movie Title',
            'year': 'Date Released'
        }
        
        column = sort_columns.get(sort_by.lower(), 'Total Gross')
        
        if sort_by.lower() == 'year':
            return data.sort_values('Date Released', ascending=ascending)
        else:
            return data.sort_values(column, ascending=ascending)
    
    def display(self, data, limit=None, format='table'):
        """Display the results"""
        if len(data) == 0:
            print("❌ No movies found")
            return
        
        # Select and rename columns for display
        display_df = data[['Movie Title', 'Date Released', 'Genre', 'Season', 
                        'MPAA Rating', 'Total Gross', 'Inflation Adjusted Gross']].copy()
        
        # Format the dates
        display_df['Date Released'] = display_df['Date Released'].dt.strftime('%d/%m/%Y')
        
        # Format the currency
        display_df['Total Gross'] = display_df['Total Gross'].apply(lambda x: f"${x:,.0f}")
        display_df['Inflation Adjusted Gross'] = display_df['Inflation Adjusted Gross'].apply(lambda x: f"${x:,.0f}")
        
        if limit:
            display_df = display_df.head(limit)
        
        if format == 'csv':
            print(display_df.to_csv(index=False))
            return
        
        # Pretty table format
        print("\n" + "="*140)
        print(f"FOUND {len(data)} MOVIES" + (f" (showing top {limit})" if limit else ""))
        print("="*140)
        
        # Calculate column widths
        title_width = max(display_df['Movie Title'].str.len().max(), 25)
        genre_width = max(display_df['Genre'].str.len().max(), 15)
        date_width = 12
        season_width = 8
        rating_width = 6
        gross_width = 18
        inflation_width = 22
        
        # Print header
        header = (f"{'TITLE':<{title_width}} {'DATE':<{date_width}} "
                f"{'SEASON':<{season_width}} {'GENRE':<{genre_width}} {'RATING':<{rating_width}} "
                f"{'TOTAL GROSS':>{gross_width}} {'INFLATION ADJ':>{inflation_width}}")
        print(header)
        print("-" * (title_width + genre_width + date_width + season_width + rating_width + gross_width + inflation_width + 10))
        
        # Print rows
        for _, row in display_df.iterrows():
            line = (f"{row['Movie Title'][:title_width-2]:<{title_width}} "
                f"{row['Date Released']:<{date_width}} "
                f"{row['Season']:<{season_width}} "
                f"{row['Genre'][:genre_width-2]:<{genre_width}} "
                f"{row['MPAA Rating']:<{rating_width}} "
                f"{row['Total Gross']:>{gross_width}} "
                f"{row['Inflation Adjusted Gross']:>{inflation_width}}")
            print(line)
        
        print("="*140)

def main():
    parser = argparse.ArgumentParser(description='🎬 Movie Database Query Tool')
    parser.add_argument('--genre', '-g', help='Filter by genre (e.g., "Action", "Comedy")')
    parser.add_argument('--season', '-s', choices=['Winter', 'Spring', 'Summer', 'Fall'], 
                       help='Filter by season')
    parser.add_argument('--years', '-y', help='Year or year range (e.g., 1994 or 1990-1999)')
    parser.add_argument('--rating', '-r', choices=['G', 'PG', 'PG-13', 'R', 'NC-17'], 
                       help='Filter by MPAA rating')
    parser.add_argument('--min-gross', '-m', type=float, 
                       help='Minimum total gross in millions (e.g., 100 for $100M)')
    
    parser.add_argument('--sort', choices=['gross', 'inflation', 'date', 'title', 'year'],
                       default='inflation', help='Sort by (default: inflation)')
    parser.add_argument('--asc', action='store_true', 
                       help='Sort ascending (default: descending)')
    parser.add_argument('--limit', '-l', type=int, default=20, 
                       help='Number of results to show (default: 20)')
    parser.add_argument('--csv', action='store_true', 
                       help='Output as CSV format')
    parser.add_argument('--file', '-f', default='disney movie total gross.csv', 
                       help='CSV file path (default: disney movie total gross.csv)')
    parser.add_argument('--info', action='store_true', 
                       help='Show database info and exit')
    
    args = parser.parse_args()
    
    # Initialize database
    db = MovieDB(args.file)
    
    # Show info if requested
    if args.info:
        print("\n📊 DATABASE INFO")
        print("="*40)
        print(f"Total movies: {len(db.df)}")
        print(f"Date range: {db.df['Date Released'].min().year} - {db.df['Date Released'].max().year}")
        print(f"\nMovies by season:")
        print(db.df['Season'].value_counts().to_string())
        print(f"\nMovies by rating:")
        print(db.df['MPAA Rating'].value_counts().to_string())
        print(f"\nTop 10 genres:")
        # Simple genre counting
        from collections import Counter
        all_genres = []
        for genres in db.df['Genre'].dropna():
            all_genres.extend([g.strip() for g in genres.split(',')])
        for genre, count in Counter(all_genres).most_common(10):
            print(f"  {genre}: {count}")
        return
    
    # Parse year/year range
    year = None
    year_start = None
    year_end = None
    
    if args.years:
        if '-' in args.years:
            parts = args.years.split('-')
            year_start = int(parts[0])
            year_end = int(parts[1])
            print(f"📅 Filtering years: {year_start}-{year_end}", file=sys.stderr)
        else:
            year = int(args.years)
            print(f"📅 Filtering year: {year}", file=sys.stderr)
    
    # Show message if no filters applied
    if not any([args.genre, args.season, args.years, args.rating, args.min_gross]):
        print("\n📋 No filters specified - showing ALL movies", file=sys.stderr)
        print("   (Use --genre, --season, --years, etc. to filter)", file=sys.stderr)
    
    # Apply filters
    filtered = db.filter(
        genre=args.genre,
        season=args.season,
        year=year,
        year_start=year_start,
        year_end=year_end,
        rating=args.rating,
        min_gross=args.min_gross
    )
    
    # Sort results
    sorted_results = db.sort(filtered, sort_by=args.sort, ascending=args.asc)
    
    # Display results
    db.display(sorted_results, limit=args.limit, format='csv' if args.csv else 'table')

if __name__ == '__main__':
    main()