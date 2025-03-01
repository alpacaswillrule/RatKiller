# Rat Reporter

A community-based application for reporting and tracking garbage disposal to help reduce rat populations in urban areas.

## Features

- **Home Page**: View your ELO rating, rank, and time until the next garbage pickup
- **311 Tab**: Report rat sightings and garbage issues to city services
- **History Tab**: View your garbage disposal history and stats
- **Friends Tab**: Connect with neighbors and compete on the leaderboard

## Screenshots

The application includes several key screens:

- Home screen with ELO rating, rank icon, and garbage timer
- 311 reporting interface for community issues
- History page showing past garbage disposals
- Friends and leaderboard for community competition

## Technical Details

### Frontend

- HTML5, CSS3, and JavaScript
- Mobile-responsive design
- Camera integration for photo uploads

### Backend

- Python Flask API
- CSV-based data storage
- RESTful endpoints for all application features

## Getting Started

### Prerequisites

- Python 3.8+
- Web browser with camera access

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rat-reporter.git
   cd rat-reporter
   ```

2. Install the required Python packages:
   ```
   pip install -r backend/requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. **Home Page**:
   - View your current ELO rating and rank
   - Check the time until the next garbage pickup
   - Click "Put Garbage Out" to take a photo

2. **311 Tab**:
   - Chat with city services
   - Submit reports about rat sightings or garbage issues

3. **History Tab**:
   - View your garbage disposal history
   - See stats on your ELO gains and timing

4. **Friends Tab**:
   - Add friends to compare stats
   - View the neighborhood leaderboard

## How ELO Works

The ELO system rewards users for proper garbage disposal:

- The closer to garbage pickup time you put out trash, the more ELO you gain
- Taking photos provides proof of proper disposal
- Compete with friends for the highest ranking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
