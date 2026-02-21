interface Batter {
  index?: number;
  common_name: string;
  unique_name: string;
  img_url: string;
}

const batterData: Batter[] = [
  {
    index: 0,
    common_name: "Dasun Shanaka",
    unique_name: "MD Shanaka",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/328000/328058.2.png",
  },
  {
    index: 1,
    common_name: "Charith Asalanka",
    unique_name: "KIC Asalanka",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/348500/348599.1.png",
  },
  {
    index: 2,
    common_name: "Dushmantha Chameera",
    unique_name: "PVD Chameera",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/319800/319862.2.png",
  },
  {
    index: 3,
    common_name: "Dushan Hemantha",
    unique_name: "MADI Hemantha",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/390700/390714.2.png",
  },
  {
    index: 4,
    common_name: "Janith Liyanage",
    unique_name: "J Liyanage",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/393400/393461.2.png",
  },
  {
    index: 5,
    common_name: "Dilshan Madushanka",
    unique_name: "LD Madushanka",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/348600/348600.1.png",
  },
  {
    index: 6,
    common_name: "Kamindu Mendis",
    unique_name: "PHKD Mendis",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/329900/329938.1.png",
  },
  {
    index: 7,
    common_name: "Kusal Mendis",
    unique_name: "BKG Mendis",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/319800/319866.2.png",
  },
  {
    index: 8,
    common_name: "Kamil Mishara",
    unique_name: "K Mishara",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_h_100_2x/lsci/db/PICTURES/CMS/334700/334794.gif",
  },
  {
    index: 9,
    common_name: "Pathum Nissanka",
    unique_name: "P Nissanka",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/323000/323070.1.png",
  },
  {
    index: 10,
    common_name: "Kusal Perera",
    unique_name: "MDKJ Perera",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/329700/329750.1.png",
  },
  {
    index: 11,
    common_name: "Pramod Madushan",
    unique_name: "PM Liyanagamage",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/355400/355401.1.png",
  },
  {
    index: 12,
    common_name: "Pavan Rathnayake",
    unique_name: "P Rathnayake",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_h_100_2x/lsci/db/PICTURES/CMS/405800/405870.gif",
  },
  {
    index: 13,
    common_name: "Maheesh Theekshana",
    unique_name: "M Theekshana",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/347800/347825.1.png",
  },
  {
    index: 14,
    common_name: "Dunith Wellalage",
    unique_name: "DN Wellalage",
    img_url:
      "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_320,q_50/lsci/db/PICTURES/CMS/380400/380446.1.png",
  },
];

interface Venue {
  name: string;
  venueType: string;
}

const venueData: Venue[] = [
  { name: "Adelaide Oval", venueType: "Neutral" },
  { name: "Barabati Stadium", venueType: "Neutral" },
  { name: "Bay Oval", venueType: "Neutral" },
  { name: "Bay Oval, Mount Maunganui", venueType: "Neutral" },
  { name: "Beausejour Stadium, Gros Islet", venueType: "Neutral" },
  { name: "Bellerive Oval, Hobart", venueType: "Neutral" },
  {
    name: "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow",
    venueType: "Neutral",
  },
  { name: "Brisbane Cricket Ground, Woolloongabba", venueType: "Neutral" },
  {
    name: "Central Broward Regional Park Stadium Turf Ground",
    venueType: "Neutral",
  },
  { name: "Coolidge Cricket Ground, Antigua", venueType: "Spin Friendly" },
  { name: "County Ground", venueType: "Neutral" },
  {
    name: "Daren Sammy National Cricket Stadium, Gros Islet, St Lucia",
    venueType: "Neutral",
  },
  {
    name: "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    venueType: "Neutral",
  },
  { name: "Dubai International Cricket Stadium", venueType: "Neutral" },
  { name: "Eden Park", venueType: "Neutral" },
  { name: "Eden Park, Auckland", venueType: "Neutral" },
  { name: "Feroz Shah Kotla", venueType: "Neutral" },
  { name: "Gaddafi Stadium", venueType: "Pace Friendly" },
  {
    name: "GMHBA Stadium, South Geelong, Victoria",
    venueType: "Spin Friendly",
  },
  { name: "Grand Prairie Stadium, Dallas", venueType: "Neutral" },
  { name: "Harare Sports Club", venueType: "Neutral" },
  {
    name: "Himachal Pradesh Cricket Association Stadium, Dharamsala",
    venueType: "Neutral",
  },
  { name: "Holkar Cricket Stadium", venueType: "Neutral" },
  { name: "John Davies Oval, Queenstown", venueType: "Neutral" },
  { name: "JSCA International Stadium Complex", venueType: "Neutral" },
  { name: "Kennington Oval", venueType: "Neutral" },
  { name: "Kensington Oval, Bridgetown", venueType: "Neutral" },
  { name: "Lord's", venueType: "Pace Friendly" },
  { name: "M Chinnaswamy Stadium", venueType: "Neutral" },
  { name: "Maharashtra Cricket Association Stadium", venueType: "Neutral" },
  {
    name: "Maharashtra Cricket Association Stadium, Pune",
    venueType: "Neutral",
  },
  {
    name: "Mahinda Rajapaksa International Cricket Stadium, Sooriyawewa",
    venueType: "Spin Friendly",
  },
  { name: "Manuka Oval, Canberra", venueType: "Neutral" },
  { name: "Maple Leaf North-West Ground", venueType: "Neutral" },
  { name: "Melbourne Cricket Ground", venueType: "Pace Friendly" },
  {
    name: "Nassau County International Cricket Stadium, New York",
    venueType: "Neutral",
  },
  { name: "New Wanderers Stadium", venueType: "Neutral" },
  { name: "Newlands", venueType: "Spin Friendly" },
  { name: "Pallekele International Cricket Stadium", venueType: "Neutral" },
  { name: "Perth Stadium", venueType: "Neutral" },
  { name: "Providence Stadium", venueType: "Neutral" },
  { name: "Punjab Cricket Association Stadium, Mohali", venueType: "Neutral" },
  { name: "R Premadasa Stadium", venueType: "Spin Friendly" },
  { name: "R Premadasa Stadium, Colombo", venueType: "Spin Friendly" },
  { name: "R.Premadasa Stadium, Khettarama", venueType: "Spin Friendly" },
  { name: "Rangiri Dambulla International Stadium", venueType: "Neutral" },
  { name: "Rawalpindi Cricket Stadium", venueType: "Spin Friendly" },
  {
    name: "Saurashtra Cricket Association Stadium, Rajkot",
    venueType: "Neutral",
  },
  { name: "Saxton Oval, Nelson", venueType: "Neutral" },
  { name: "Sharjah Cricket Stadium", venueType: "Spin Friendly" },
  { name: "Sheikh Zayed Stadium", venueType: "Pace Friendly" },
  { name: "Shere Bangla National Stadium", venueType: "Pace Friendly" },
  { name: "Shere Bangla National Stadium, Mirpur", venueType: "Neutral" },
  { name: "Simonds Stadium, South Geelong", venueType: "Neutral" },
  { name: "Sophia Gardens, Cardiff", venueType: "Neutral" },
  { name: "Stadium Australia", venueType: "Neutral" },
  { name: "SuperSport Park", venueType: "Neutral" },
  { name: "Sydney Cricket Ground", venueType: "Neutral" },
  { name: "Sylhet International Cricket Stadium", venueType: "Neutral" },
  { name: "The Rose Bowl", venueType: "Neutral" },
  { name: "The Rose Bowl, Southampton", venueType: "Neutral" },
  { name: "The Wanderers Stadium", venueType: "Neutral" },
  { name: "Trent Bridge", venueType: "Spin Friendly" },
  { name: "University Oval, Dunedin", venueType: "Neutral" },
  {
    name: "Vidarbha Cricket Association Stadium, Jamtha",
    venueType: "Neutral",
  },
  { name: "Wankhede Stadium", venueType: "Neutral" },
  { name: "Wankhede Stadium, Mumbai", venueType: "Neutral" },
  {
    name: "Western Australia Cricket Association Ground",
    venueType: "Neutral",
  },
  { name: "Westpac Stadium", venueType: "Neutral" },
  { name: "Zahur Ahmed Chowdhury Stadium", venueType: "Spin Friendly" },
  { name: "Zayed Cricket Stadium, Abu Dhabi", venueType: "Spin Friendly" },
];

interface BowlerGroup {
  type: string;
}

const bowlerGroups: BowlerGroup[] = [
  { type: "Pace" },
  { type: "Off-Spin" },
  { type: "Leg-Spin" },
  { type: "Left-Arm Orthodox" },
];

export { batterData, venueData, bowlerGroups };
