import pandas as pd
import argparse
import sys
import re
from datetime import datetime

class MovieFilter:
    def __init__(self, csv_file='movies.csv'):
        """Load the movie database"""
        try:
            self.df = pd.read_csv(csv_file)
            
            # Convert numeric columns
            numeric_cols = ['year', 'budget', 'gross', 'votes', 'score']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Format the release date to dd/mm/yyyy
            if 'released' in self.df.columns:
                self.df['released'] = self.df['released'].apply(self.format_date)
            
            # Rename columns to match desired output
            self.df = self.df.rename(columns={
                'name': 'Movie Title',
                'released': 'Date Released',
                'genre': 'Genre',
                'rating': 'MPAA Rating',
                'gross': 'Total Gross',
                'company': 'Company'
            })
            
            print(f"✅ Loaded {len(self.df)} movies from {csv_file}", file=sys.stderr)
            
        except FileNotFoundError:
            print(f"❌ Error: {csv_file} not found!", file=sys.stderr)
            sys.exit(1)
    
    def format_date(self, date_str):
        """Convert date from various formats to dd/mm/yyyy"""
        if pd.isna(date_str) or date_str == 'N/A':
            return 'N/A'
        
        try:
            # Try to parse the date - handles formats like "June 13, 1980 (United States)"
            # First, extract just the date part before any parenthesis
            date_part = re.sub(r'\s*\([^)]*\)', '', str(date_str)).strip()
            
            # Try different date formats
            for fmt in ('%B %d, %Y', '%b %d, %Y', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(date_part, fmt)
                    return dt.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            
            # If all else fails, return original
            return date_str
        except:
            return date_str
    
    def filter(self, genre=None, rating=None, year=None, year_start=None, year_end=None,
              director=None, star=None, country=None, company=None,
              min_score=None, min_gross=None, min_votes=None):
        """Apply filters to the database"""
        result = self.df.copy()
        
        if genre and 'Genre' in result.columns:
            result = result[result['Genre'].str.contains(genre, case=False, na=False)]
        if rating and 'MPAA Rating' in result.columns:
            result = result[result['MPAA Rating'] == rating.upper()]
        if year and 'year' in result.columns:
            result = result[result['year'] == year]
        if year_start and year_end and 'year' in result.columns:
            result = result[(result['year'] >= year_start) & (result['year'] <= year_end)]
        if director and 'director' in result.columns:
            result = result[result['director'].str.contains(director, case=False, na=False)]
        if star and 'star' in result.columns:
            result = result[result['star'].str.contains(star, case=False, na=False)]
        if country and 'country' in result.columns:
            result = result[result['country'].str.contains(country, case=False, na=False)]
        if company and 'Company' in result.columns:
            result = result[result['Company'].str.contains(company, case=False, na=False)]
        if min_score and 'score' in result.columns:
            result = result[result['score'] >= min_score]
        if min_gross and 'Total Gross' in result.columns:
            result = result[result['Total Gross'] >= min_gross]
        if min_votes and 'votes' in result.columns:
            result = result[result['votes'] >= min_votes]
        
        return result
    
    def sort(self, data, by='gross', ascending=False):
        """Sort the filtered data"""
        sort_map = {
            'name': 'Movie Title',
            'year': 'year',
            'rating': 'MPAA Rating',
            'gross': 'Total Gross',
            'budget': 'budget',
            'votes': 'votes',
            'released': 'Date Released'
        }
        
        sort_col = sort_map.get(by.lower(), 'Total Gross')
        if sort_col in data.columns:
            return data.sort_values(by=sort_col, ascending=ascending)
        return data
    
    def display(self, data, limit=20, format='table'):
        """Display the results"""
        if len(data) == 0:
            print("❌ No movies found")
            return
        
        # Select display columns
        display_cols = ['Movie Title', 'year', 'Date Released', 'MPAA Rating', 'Genre', 'Total Gross', 'Company']
        available_cols = [col for col in display_cols if col in data.columns]
        
        display_df = data[available_cols].head(limit).copy()
        
        # Format gross with commas for display (but keep as int in data)
        if 'Total Gross' in display_df.columns:
            display_df['Total Gross'] = display_df['Total Gross'].apply(
                lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else 'N/A'
            )
        
        if format == 'csv':
            # For CSV output, use EXACT format requested: Movie Title,Date Released,Genre,MPAA Rating,Total Gross,0
            csv_cols = ['Movie Title', 'Date Released', 'Genre', 'MPAA Rating', 'Total Gross']
            available_csv = [col for col in csv_cols if col in data.columns]
            
            csv_df = data[available_csv].copy()
            
            # Format Total Gross as raw integer (NO commas)
            if 'Total Gross' in csv_df.columns:
                csv_df['Total Gross'] = csv_df['Total Gross'].apply(
                    lambda x: str(int(x)) if pd.notna(x) and x != '' else ''
                )
                
            # Add the ",0" column for inflation adjusted gross (to be filled later)
            csv_df['Inflation Adjusted Gross'] = '0'
            
            # Reorder to match exact format
            final_df = csv_df[['Movie Title', 'Date Released', 'Genre', 'MPAA Rating', 'Total Gross', 'Inflation Adjusted Gross']]
            
            print(final_df.to_csv(index=False))
            return
        
        # Pretty table format
        print("\n" + "="*130)
        print(f"📽️  FOUND {len(data)} MOVIES" + (f" (showing top {limit})" if limit else ""))
        print("="*130)
        
        # Calculate column widths
        col_widths = {}
        for col in available_cols:
            max_len = max(
                display_df[col].astype(str).str.len().max(),
                len(col)
            )
            col_widths[col] = min(max_len + 2, 25)
        
        # Print header
        header = "  ".join([f"{col:<{col_widths[col]}}" for col in available_cols])
        print(header)
        print("-"*130)
        
        # Print rows
        for _, row in display_df.iterrows():
            line = "  ".join([
                f"{str(row[col])[:col_widths[col]-2]:<{col_widths[col]}}" 
                for col in available_cols
            ])
            print(line)
        
        print("="*130)
    
    def save_to_csv(self, data, filename='filtered_movies.csv'):
        """Save filtered results to CSV file in the requested format"""
        if len(data) == 0:
            print("❌ No data to save")
            return
        
        # Save in format: Movie Title,Date Released,Genre,MPAA Rating,Total Gross,0
        save_cols = ['Movie Title', 'Date Released', 'Genre', 'MPAA Rating', 'Total Gross']
        available_cols = [col for col in save_cols if col in data.columns]
        
        save_df = data[available_cols].copy()
        
        # Format Total Gross as raw integer (NO commas)
        if 'Total Gross' in save_df.columns:
            save_df['Total Gross'] = save_df['Total Gross'].apply(
                lambda x: str(int(x)) if pd.notna(x) and x != '' else ''
            )
        
        # Add the ",0" column for inflation adjusted gross (to be filled later)
        save_df['Inflation Adjusted Gross'] = '0'
        
        # Reorder to match exact format
        final_df = save_df[['Movie Title', 'Date Released', 'Genre', 'MPAA Rating', 'Total Gross', 'Inflation Adjusted Gross']]
        
        final_df.to_csv(filename, index=False)
        print(f"✅ Saved {len(final_df)} movies to {filename}")

def main():
    parser = argparse.ArgumentParser(description='🎬 Movie Database Query Tool')
    
    # Filter arguments
    parser.add_argument('--genre', '-g', help='Filter by genre')
    parser.add_argument('--rating', '-r', choices=['G', 'PG', 'PG-13', 'R', 'NC-17', 'Unknown'],
                       help='Filter by MPAA rating')
    parser.add_argument('--year', '-y', type=int, help='Filter by specific year')
    parser.add_argument('--year-range', '-yr', help='Year range (e.g., 1990-1999)')
    parser.add_argument('--director', '-d', help='Filter by director')
    parser.add_argument('--star', '-s', help='Filter by lead actor/star')
    parser.add_argument('--country', '-c', help='Filter by country of origin')
    parser.add_argument('--company', '-co', help='Filter by production company')
    parser.add_argument('--min-score', '-sc', type=float, help='Minimum IMDb score (0-10)')
    parser.add_argument('--min-gross', '-mg', type=float, 
                       help='Minimum gross in millions (e.g., 100 for $100M)')
    parser.add_argument('--min-votes', '-mv', type=int, help='Minimum number of votes')
    
    # Sorting arguments
    parser.add_argument('--sort', choices=['name', 'year', 'rating', 'gross', 'budget', 'votes', 'released'],
                       default='gross', help='Sort by (default: gross)')
    parser.add_argument('--asc', action='store_true', help='Sort ascending (default: descending)')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Number of results (default: 20)')
    
    # Output arguments
    parser.add_argument('--csv', action='store_true', help='Output as CSV format')
    parser.add_argument('--save', '-sv', help='Save results to CSV file (provide filename)')
    parser.add_argument('--file', '-f', default='movies.csv', help='CSV file path (default: movies.csv)')
    parser.add_argument('--info', action='store_true', help='Show database info and exit')
    parser.add_argument('--columns', action='store_true', help='Show available columns and exit')
    
    args = parser.parse_args()
    
    # Initialize filter
    filter_tool = MovieFilter(args.file)
    
    # Show info if requested
    if args.info:
        print("\n📊 DATABASE INFO")
        print("="*40)
        print(f"Total movies: {len(filter_tool.df)}")
        print(f"\nColumns available:")
        for col in filter_tool.df.columns:
            print(f"  • {col}")
        
        if 'year' in filter_tool.df.columns:
            print(f"\nYear range: {int(filter_tool.df['year'].min())} - {int(filter_tool.df['year'].max())}")
        if 'MPAA Rating' in filter_tool.df.columns:
            print(f"\nRatings: {filter_tool.df['MPAA Rating'].value_counts().to_dict()}")
        return
    
    if args.columns:
        print("\n📋 AVAILABLE COLUMNS")
        print("="*40)
        for col in filter_tool.df.columns:
            print(f"  • {col}")
        return
    
    # Parse year range
    year = args.year
    year_start = None
    year_end = None
    
    if args.year_range:
        try:
            parts = args.year_range.split('-')
            year_start = int(parts[0])
            year_end = int(parts[1]) if len(parts) > 1 else year_start
        except:
            print("❌ Invalid year range format. Use YYYY-YYYY", file=sys.stderr)
            sys.exit(1)
    
    # Show message if no filters applied
    filters_applied = any([args.genre, args.rating, args.year, args.year_range, 
                          args.director, args.star, args.country, args.company,
                          args.min_score, args.min_gross, args.min_votes])
    
    if not filters_applied:
        print("\n📋 No filters specified - showing ALL movies", file=sys.stderr)
    
    # Apply filters
    filtered = filter_tool.filter(
        genre=args.genre,
        rating=args.rating,
        year=year,
        year_start=year_start,
        year_end=year_end,
        director=args.director,
        star=args.star,
        country=args.country,
        company=args.company,
        min_score=args.min_score,
        min_gross=args.min_gross * 1_000_000 if args.min_gross else None,
        min_votes=args.min_votes
    )
    
    # Sort results
    sorted_results = filter_tool.sort(filtered, by=args.sort, ascending=args.asc)
    
    # Save to file if requested
    if args.save:
        filter_tool.save_to_csv(sorted_results, args.save)
    
    # Display results (unless we're just saving)
    if not args.save or args.csv:
        filter_tool.display(sorted_results, limit=args.limit, format='csv' if args.csv else 'table')

if __name__ == "__main__":
    main()