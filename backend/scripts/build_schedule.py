import json

schedule = {
    'tournament': '2026年美加墨世界杯',
    'tournament_en': '2026 FIFA World Cup',
    'hosts': ['United States', 'Canada', 'Mexico'],
    'hosts_cn': ['美国', '加拿大', '墨西哥'],
    'dates': '2026-06-11 to 2026-07-19',
    'total_matches': 104,
    'teams': 48,
    'groups': 12,
    'host_cities': 16,
    'timezone_note': '小组赛时间均为北京时间(UTC+8)',
    'venues': [
        {'name': 'Estadio Azteca', 'name_cn': '阿兹特克体育场', 'city': 'Mexico City', 'city_cn': '墨西哥城', 'country': 'Mexico', 'capacity': 87523},
        {'name': 'Estadio Akron', 'name_cn': '阿克伦体育场', 'city': 'Guadalajara', 'city_cn': '瓜达拉哈拉', 'country': 'Mexico', 'capacity': 48100},
        {'name': 'Estadio BBVA', 'name_cn': 'BBVA体育场', 'city': 'Guadalupe', 'city_cn': '瓜达卢佩', 'country': 'Mexico', 'capacity': 53500},
        {'name': 'BMO Field', 'name_cn': 'BMO球场', 'city': 'Toronto', 'city_cn': '多伦多', 'country': 'Canada', 'capacity': 45500},
        {'name': 'BC Place', 'name_cn': 'BC Place体育场', 'city': 'Vancouver', 'city_cn': '温哥华', 'country': 'Canada', 'capacity': 54500},
        {'name': 'MetLife Stadium', 'name_cn': '大都会人寿体育场', 'city': 'East Rutherford', 'city_cn': '东卢瑟福(纽约)', 'country': 'USA', 'capacity': 82500},
        {'name': 'AT&T Stadium', 'name_cn': 'AT&T体育场', 'city': 'Arlington', 'city_cn': '阿灵顿(达拉斯)', 'country': 'USA', 'capacity': 105000},
        {'name': 'SoFi Stadium', 'name_cn': 'SoFi体育场', 'city': 'Inglewood', 'city_cn': '英格尔伍德(洛杉矶)', 'country': 'USA', 'capacity': 70240},
        {'name': "Levi's Stadium", 'name_cn': '李维斯体育场', 'city': 'Santa Clara', 'city_cn': '圣克拉拉(旧金山)', 'country': 'USA', 'capacity': 68500},
        {'name': 'Mercedes-Benz Stadium', 'name_cn': '梅赛德斯-奔驰体育场', 'city': 'Atlanta', 'city_cn': '亚特兰大', 'country': 'USA', 'capacity': 71000},
        {'name': 'NRG Stadium', 'name_cn': 'NRG体育场', 'city': 'Houston', 'city_cn': '休斯顿', 'country': 'USA', 'capacity': 72220},
        {'name': 'Arrowhead Stadium', 'name_cn': '箭头体育场', 'city': 'Kansas City', 'city_cn': '堪萨斯城', 'country': 'USA', 'capacity': 76416},
        {'name': 'Hard Rock Stadium', 'name_cn': '硬石体育场', 'city': 'Miami Gardens', 'city_cn': '迈阿密花园', 'country': 'USA', 'capacity': 65326},
        {'name': 'Lincoln Financial Field', 'name_cn': '林肯金融球场', 'city': 'Philadelphia', 'city_cn': '费城', 'country': 'USA', 'capacity': 67594},
        {'name': 'Lumen Field', 'name_cn': '流明球场', 'city': 'Seattle', 'city_cn': '西雅图', 'country': 'USA', 'capacity': 68740},
        {'name': 'Gillette Stadium', 'name_cn': '吉列体育场', 'city': 'Foxborough', 'city_cn': '福克斯堡(波士顿)', 'country': 'USA', 'capacity': 65878}
    ],
    'matches': []
}

def m(match_id, stage, group, round_num, date_bj, time_bj, home, away, home_cn, away_cn, venue, city, country, note=''):
    return {
        'match_id': match_id,
        'stage': stage,
        'group': group,
        'round': round_num,
        'date': date_bj,
        'time_bj': time_bj,
        'home_team': home,
        'away_team': away,
        'home_team_cn': home_cn,
        'away_team_cn': away_cn,
        'venue': venue,
        'city': city,
        'country': country,
        'note': note
    }

# ============ GROUP STAGE (72 matches) ============

# --- Round 1 ---
schedule['matches'].append(m(1, 'group', 'A', 1, '2026-06-12', '03:00', 'Mexico', 'South Africa', '墨西哥', '南非', 'Estadio Azteca', 'Mexico City', 'Mexico', '揭幕战'))
schedule['matches'].append(m(2, 'group', 'A', 1, '2026-06-12', '10:00', 'South Korea', 'Czech Republic', '韩国', '捷克', 'Estadio Akron', 'Guadalajara', 'Mexico'))
schedule['matches'].append(m(3, 'group', 'B', 1, '2026-06-13', '03:00', 'Canada', 'Bosnia and Herzegovina', '加拿大', '波黑', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(4, 'group', 'D', 1, '2026-06-13', '09:00', 'United States', 'Paraguay', '美国', '巴拉圭', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(5, 'group', 'B', 1, '2026-06-14', '03:00', 'Qatar', 'Switzerland', '卡塔尔', '瑞士', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(6, 'group', 'C', 1, '2026-06-14', '06:00', 'Brazil', 'Morocco', '巴西', '摩洛哥', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(7, 'group', 'C', 1, '2026-06-14', '09:00', 'Haiti', 'Scotland', '海地', '苏格兰', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(8, 'group', 'D', 1, '2026-06-14', '12:00', 'Australia', 'Turkey', '澳大利亚', '土耳其', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(9, 'group', 'E', 1, '2026-06-15', '01:00', 'Germany', 'Curaçao', '德国', '库拉索', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(10, 'group', 'F', 1, '2026-06-15', '04:00', 'Netherlands', 'Japan', '荷兰', '日本', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(11, 'group', 'E', 1, '2026-06-15', '07:00', 'Ivory Coast', 'Ecuador', '科特迪瓦', '厄瓜多尔', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(12, 'group', 'F', 1, '2026-06-15', '10:00', 'Sweden', 'Tunisia', '瑞典', '突尼斯', 'Estadio BBVA', 'Guadalupe', 'Mexico'))
schedule['matches'].append(m(13, 'group', 'H', 1, '2026-06-16', '00:00', 'Spain', 'Cape Verde', '西班牙', '佛得角', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(14, 'group', 'G', 1, '2026-06-16', '03:00', 'Belgium', 'Egypt', '比利时', '埃及', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(15, 'group', 'H', 1, '2026-06-16', '06:00', 'Saudi Arabia', 'Uruguay', '沙特阿拉伯', '乌拉圭', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(16, 'group', 'G', 1, '2026-06-16', '09:00', 'Iran', 'New Zealand', '伊朗', '新西兰', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(17, 'group', 'I', 1, '2026-06-17', '03:00', 'France', 'Senegal', '法国', '塞内加尔', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(18, 'group', 'I', 1, '2026-06-17', '06:00', 'Iraq', 'Norway', '伊拉克', '挪威', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(19, 'group', 'J', 1, '2026-06-17', '09:00', 'Argentina', 'Algeria', '阿根廷', '阿尔及利亚', 'Arrowhead Stadium', 'Kansas City', 'USA'))
schedule['matches'].append(m(20, 'group', 'J', 1, '2026-06-17', '12:00', 'Austria', 'Jordan', '奥地利', '约旦', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(21, 'group', 'K', 1, '2026-06-18', '01:00', 'Portugal', 'DR Congo', '葡萄牙', '民主刚果', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(22, 'group', 'L', 1, '2026-06-18', '04:00', 'England', 'Croatia', '英格兰', '克罗地亚', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(23, 'group', 'L', 1, '2026-06-18', '07:00', 'Ghana', 'Panama', '加纳', '巴拿马', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(24, 'group', 'K', 1, '2026-06-18', '10:00', 'Uzbekistan', 'Colombia', '乌兹别克斯坦', '哥伦比亚', 'Estadio Azteca', 'Mexico City', 'Mexico'))

# --- Round 2 ---
schedule['matches'].append(m(25, 'group', 'A', 2, '2026-06-19', '00:00', 'Czech Republic', 'South Africa', '捷克', '南非', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(26, 'group', 'B', 2, '2026-06-19', '03:00', 'Switzerland', 'Bosnia and Herzegovina', '瑞士', '波黑', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(27, 'group', 'B', 2, '2026-06-19', '06:00', 'Canada', 'Qatar', '加拿大', '卡塔尔', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(28, 'group', 'A', 2, '2026-06-19', '09:00', 'Mexico', 'South Korea', '墨西哥', '韩国', 'Estadio Akron', 'Guadalajara', 'Mexico'))
schedule['matches'].append(m(29, 'group', 'D', 2, '2026-06-20', '03:00', 'United States', 'Australia', '美国', '澳大利亚', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(30, 'group', 'C', 2, '2026-06-20', '06:00', 'Scotland', 'Morocco', '苏格兰', '摩洛哥', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(31, 'group', 'C', 2, '2026-06-20', '09:00', 'Brazil', 'Haiti', '巴西', '海地', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(32, 'group', 'D', 2, '2026-06-20', '12:00', 'Turkey', 'Paraguay', '土耳其', '巴拉圭', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(33, 'group', 'F', 2, '2026-06-21', '01:00', 'Netherlands', 'Sweden', '荷兰', '瑞典', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(34, 'group', 'E', 2, '2026-06-21', '04:00', 'Germany', 'Ivory Coast', '德国', '科特迪瓦', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(35, 'group', 'E', 2, '2026-06-21', '08:00', 'Ecuador', 'Curaçao', '厄瓜多尔', '库拉索', 'Arrowhead Stadium', 'Kansas City', 'USA'))
schedule['matches'].append(m(36, 'group', 'F', 2, '2026-06-21', '12:00', 'Tunisia', 'Japan', '突尼斯', '日本', 'Estadio BBVA', 'Guadalupe', 'Mexico'))
schedule['matches'].append(m(37, 'group', 'H', 2, '2026-06-22', '00:00', 'Spain', 'Saudi Arabia', '西班牙', '沙特阿拉伯', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(38, 'group', 'G', 2, '2026-06-22', '03:00', 'Belgium', 'Iran', '比利时', '伊朗', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(39, 'group', 'H', 2, '2026-06-22', '06:00', 'Uruguay', 'Cape Verde', '乌拉圭', '佛得角', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(40, 'group', 'G', 2, '2026-06-22', '09:00', 'New Zealand', 'Egypt', '新西兰', '埃及', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(41, 'group', 'J', 2, '2026-06-23', '01:00', 'Argentina', 'Austria', '阿根廷', '奥地利', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(42, 'group', 'I', 2, '2026-06-23', '05:00', 'France', 'Iraq', '法国', '伊拉克', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(43, 'group', 'I', 2, '2026-06-23', '08:00', 'Norway', 'Senegal', '挪威', '塞内加尔', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(44, 'group', 'J', 2, '2026-06-23', '11:00', 'Jordan', 'Algeria', '约旦', '阿尔及利亚', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(45, 'group', 'K', 2, '2026-06-24', '01:00', 'Portugal', 'Uzbekistan', '葡萄牙', '乌兹别克斯坦', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(46, 'group', 'L', 2, '2026-06-24', '04:00', 'England', 'Ghana', '英格兰', '加纳', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(47, 'group', 'L', 2, '2026-06-24', '07:00', 'Panama', 'Croatia', '巴拿马', '克罗地亚', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(48, 'group', 'K', 2, '2026-06-24', '10:00', 'Colombia', 'DR Congo', '哥伦比亚', '民主刚果', 'Estadio Akron', 'Guadalajara', 'Mexico'))

# --- Round 3 ---
schedule['matches'].append(m(49, 'group', 'B', 3, '2026-06-25', '03:00', 'Switzerland', 'Canada', '瑞士', '加拿大', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(50, 'group', 'B', 3, '2026-06-25', '03:00', 'Bosnia and Herzegovina', 'Qatar', '波黑', '卡塔尔', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(51, 'group', 'C', 3, '2026-06-25', '06:00', 'Scotland', 'Brazil', '苏格兰', '巴西', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(52, 'group', 'C', 3, '2026-06-25', '06:00', 'Morocco', 'Haiti', '摩洛哥', '海地', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(53, 'group', 'A', 3, '2026-06-25', '09:00', 'Czech Republic', 'Mexico', '捷克', '墨西哥', 'Estadio Azteca', 'Mexico City', 'Mexico'))
schedule['matches'].append(m(54, 'group', 'A', 3, '2026-06-25', '09:00', 'South Africa', 'South Korea', '南非', '韩国', 'Estadio BBVA', 'Guadalupe', 'Mexico'))
schedule['matches'].append(m(55, 'group', 'E', 3, '2026-06-26', '04:00', 'Ecuador', 'Germany', '厄瓜多尔', '德国', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(56, 'group', 'E', 3, '2026-06-26', '04:00', 'Curaçao', 'Ivory Coast', '库拉索', '科特迪瓦', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(57, 'group', 'F', 3, '2026-06-26', '07:00', 'Japan', 'Sweden', '日本', '瑞典', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(58, 'group', 'F', 3, '2026-06-26', '07:00', 'Tunisia', 'Netherlands', '突尼斯', '荷兰', 'Arrowhead Stadium', 'Kansas City', 'USA'))
schedule['matches'].append(m(59, 'group', 'D', 3, '2026-06-26', '10:00', 'Turkey', 'United States', '土耳其', '美国', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(60, 'group', 'D', 3, '2026-06-26', '10:00', 'Paraguay', 'Australia', '巴拉圭', '澳大利亚', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(61, 'group', 'I', 3, '2026-06-27', '03:00', 'Norway', 'France', '挪威', '法国', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(62, 'group', 'I', 3, '2026-06-27', '03:00', 'Senegal', 'Iraq', '塞内加尔', '伊拉克', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(63, 'group', 'H', 3, '2026-06-27', '08:00', 'Cape Verde', 'Saudi Arabia', '佛得角', '沙特阿拉伯', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(64, 'group', 'H', 3, '2026-06-27', '08:00', 'Uruguay', 'Spain', '乌拉圭', '西班牙', 'Estadio Akron', 'Guadalajara', 'Mexico'))
schedule['matches'].append(m(65, 'group', 'G', 3, '2026-06-27', '11:00', 'Egypt', 'Iran', '埃及', '伊朗', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(66, 'group', 'G', 3, '2026-06-27', '11:00', 'New Zealand', 'Belgium', '新西兰', '比利时', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(67, 'group', 'L', 3, '2026-06-28', '05:00', 'Panama', 'England', '巴拿马', '英格兰', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(68, 'group', 'L', 3, '2026-06-28', '05:00', 'Croatia', 'Ghana', '克罗地亚', '加纳', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(69, 'group', 'K', 3, '2026-06-28', '07:30', 'Colombia', 'Portugal', '哥伦比亚', '葡萄牙', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(70, 'group', 'K', 3, '2026-06-28', '07:30', 'DR Congo', 'Uzbekistan', '民主刚果', '乌兹别克斯坦', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(71, 'group', 'J', 3, '2026-06-28', '10:00', 'Algeria', 'Austria', '阿尔及利亚', '奥地利', 'Arrowhead Stadium', 'Kansas City', 'USA'))
schedule['matches'].append(m(72, 'group', 'J', 3, '2026-06-28', '10:00', 'Jordan', 'Argentina', '约旦', '阿根廷', 'AT&T Stadium', 'Arlington', 'USA'))

# ============ KNOCKOUT STAGE (32 matches) ============

# Round of 32 (16 matches)
schedule['matches'].append(m(73, 'round_of_32', '', 4, '2026-06-29', '03:00', 'A2', 'B2', 'A组第2', 'B组第2', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(74, 'round_of_32', '', 4, '2026-06-30', '01:00', 'C1', 'F2', 'C组第1', 'F组第2', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(75, 'round_of_32', '', 4, '2026-06-30', '04:30', 'E1', '3rd_ABCD', 'E组第1', 'A/B/C/D/F组第3', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(76, 'round_of_32', '', 4, '2026-06-30', '09:00', 'F1', 'C2', 'F组第1', 'C组第2', 'Estadio BBVA', 'Guadalupe', 'Mexico'))
schedule['matches'].append(m(77, 'round_of_32', '', 4, '2026-07-01', '01:00', 'E2', 'I2', 'E组第2', 'I组第2', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(78, 'round_of_32', '', 4, '2026-07-01', '05:00', 'I1', '3rd_CDFG', 'I组第1', 'C/D/F/G/H组第3', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(79, 'round_of_32', '', 4, '2026-07-01', '09:00', 'A1', '3rd_CEFH', 'A组第1', 'C/E/F/H/I组第3', 'Estadio Azteca', 'Mexico City', 'Mexico'))
schedule['matches'].append(m(80, 'round_of_32', '', 4, '2026-07-02', '00:00', 'L1', '3rd_EHIJ', 'L组第1', 'E/H/I/J/K组第3', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(81, 'round_of_32', '', 4, '2026-07-02', '04:00', 'G1', '3rd_AEHI', 'G组第1', 'A/E/H/I/J组第3', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(82, 'round_of_32', '', 4, '2026-07-02', '08:00', 'D1', '3rd_BEFI', 'D组第1', 'B/E/F/I/J组第3', "Levi's Stadium", 'Santa Clara', 'USA'))
schedule['matches'].append(m(83, 'round_of_32', '', 4, '2026-07-03', '03:00', 'H1', 'J2', 'H组第1', 'J组第2', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(84, 'round_of_32', '', 4, '2026-07-03', '07:00', 'K2', 'L2', 'K组第2', 'L组第2', 'BMO Field', 'Toronto', 'Canada'))
schedule['matches'].append(m(85, 'round_of_32', '', 4, '2026-07-03', '11:00', 'B1', '3rd_EFGI', 'B组第1', 'E/F/G/I/J组第3', 'BC Place', 'Vancouver', 'Canada'))
schedule['matches'].append(m(86, 'round_of_32', '', 4, '2026-07-04', '02:00', 'D2', 'G2', 'D组第2', 'G组第2', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(87, 'round_of_32', '', 4, '2026-07-04', '06:00', 'J1', 'H2', 'J组第1', 'H组第2', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(88, 'round_of_32', '', 4, '2026-07-04', '09:30', 'K1', '3rd_DEIJ', 'K组第1', 'D/E/I/J/L组第3', 'Arrowhead Stadium', 'Kansas City', 'USA'))

# Round of 16 (8 matches)
schedule['matches'].append(m(89, 'round_of_16', '', 5, '2026-07-05', '01:00', 'W73', 'W75', 'M73胜者', 'M75胜者', 'NRG Stadium', 'Houston', 'USA'))
schedule['matches'].append(m(90, 'round_of_16', '', 5, '2026-07-05', '05:00', 'W74', 'W77', 'M74胜者', 'M77胜者', 'Lincoln Financial Field', 'Philadelphia', 'USA'))
schedule['matches'].append(m(91, 'round_of_16', '', 5, '2026-07-06', '04:00', 'W76', 'W78', 'M76胜者', 'M78胜者', 'MetLife Stadium', 'East Rutherford', 'USA'))
schedule['matches'].append(m(92, 'round_of_16', '', 5, '2026-07-06', '08:00', 'W79', 'W80', 'M79胜者', 'M80胜者', 'Estadio Azteca', 'Mexico City', 'Mexico'))
schedule['matches'].append(m(93, 'round_of_16', '', 5, '2026-07-07', '03:00', 'W83', 'W84', 'M83胜者', 'M84胜者', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(94, 'round_of_16', '', 5, '2026-07-07', '08:00', 'W81', 'W82', 'M81胜者', 'M82胜者', 'Lumen Field', 'Seattle', 'USA'))
schedule['matches'].append(m(95, 'round_of_16', '', 5, '2026-07-08', '00:00', 'W86', 'W88', 'M86胜者', 'M88胜者', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))
schedule['matches'].append(m(96, 'round_of_16', '', 5, '2026-07-08', '04:00', 'W85', 'W87', 'M85胜者', 'M87胜者', 'BC Place', 'Vancouver', 'Canada'))

# Quarter-finals (4 matches)
schedule['matches'].append(m(97, 'quarter_final', '', 6, '2026-07-10', '04:00', 'W89', 'W90', 'M89胜者', 'M90胜者', 'Gillette Stadium', 'Foxborough', 'USA'))
schedule['matches'].append(m(98, 'quarter_final', '', 6, '2026-07-11', '03:00', 'W93', 'W94', 'M93胜者', 'M94胜者', 'SoFi Stadium', 'Inglewood', 'USA'))
schedule['matches'].append(m(99, 'quarter_final', '', 6, '2026-07-12', '05:00', 'W91', 'W92', 'M91胜者', 'M92胜者', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))
schedule['matches'].append(m(100, 'quarter_final', '', 6, '2026-07-12', '09:00', 'W95', 'W96', 'M95胜者', 'M96胜者', 'Arrowhead Stadium', 'Kansas City', 'USA'))

# Semi-finals (2 matches)
schedule['matches'].append(m(101, 'semi_final', '', 7, '2026-07-15', '03:00', 'W97', 'W98', 'M97胜者', 'M98胜者', 'AT&T Stadium', 'Arlington', 'USA'))
schedule['matches'].append(m(102, 'semi_final', '', 7, '2026-07-16', '03:00', 'W99', 'W100', 'M99胜者', 'M100胜者', 'Mercedes-Benz Stadium', 'Atlanta', 'USA'))

# Third place
schedule['matches'].append(m(103, 'third_place', '', 8, '2026-07-19', '05:00', 'L101', 'L102', 'M101负者', 'M102负者', 'Hard Rock Stadium', 'Miami Gardens', 'USA'))

# Final
schedule['matches'].append(m(104, 'final', '', 9, '2026-07-20', '03:00', 'W101', 'W102', 'M101胜者', 'M102胜者', 'MetLife Stadium', 'East Rutherford', 'USA', '决赛'))

# Groups
schedule['groups'] = {
    'A': {'name': 'A组', 'teams': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'], 'teams_cn': ['墨西哥', '南非', '韩国', '捷克']},
    'B': {'name': 'B组', 'teams': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'], 'teams_cn': ['加拿大', '波黑', '卡塔尔', '瑞士']},
    'C': {'name': 'C组', 'teams': ['Brazil', 'Morocco', 'Haiti', 'Scotland'], 'teams_cn': ['巴西', '摩洛哥', '海地', '苏格兰']},
    'D': {'name': 'D组', 'teams': ['United States', 'Paraguay', 'Australia', 'Turkey'], 'teams_cn': ['美国', '巴拉圭', '澳大利亚', '土耳其']},
    'E': {'name': 'E组', 'teams': ['Germany', 'Curaçao', 'Ivory Coast', 'Ecuador'], 'teams_cn': ['德国', '库拉索', '科特迪瓦', '厄瓜多尔']},
    'F': {'name': 'F组', 'teams': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'], 'teams_cn': ['荷兰', '日本', '瑞典', '突尼斯']},
    'G': {'name': 'G组', 'teams': ['Belgium', 'Egypt', 'Iran', 'New Zealand'], 'teams_cn': ['比利时', '埃及', '伊朗', '新西兰']},
    'H': {'name': 'H组', 'teams': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'], 'teams_cn': ['西班牙', '佛得角', '沙特阿拉伯', '乌拉圭']},
    'I': {'name': 'I组', 'teams': ['France', 'Senegal', 'Iraq', 'Norway'], 'teams_cn': ['法国', '塞内加尔', '伊拉克', '挪威']},
    'J': {'name': 'J组', 'teams': ['Argentina', 'Algeria', 'Austria', 'Jordan'], 'teams_cn': ['阿根廷', '阿尔及利亚', '奥地利', '约旦']},
    'K': {'name': 'K组', 'teams': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'], 'teams_cn': ['葡萄牙', '民主刚果', '乌兹别克斯坦', '哥伦比亚']},
    'L': {'name': 'L组', 'teams': ['England', 'Croatia', 'Ghana', 'Panama'], 'teams_cn': ['英格兰', '克罗地亚', '加纳', '巴拿马']}
}

# Knockout bracket slots
schedule['knockout_slots'] = {
    'round_of_32': list(range(73, 89)),
    'round_of_16': list(range(89, 97)),
    'quarter_final': list(range(97, 101)),
    'semi_final': [101, 102],
    'third_place': [103],
    'final': [104]
}

# Stage labels
schedule['stage_labels'] = {
    'group': {'name': '小组赛', 'name_cn': '小组赛', 'rounds': 3},
    'round_of_32': {'name': '1/16决赛', 'name_cn': '1/16决赛（32强）', 'rounds': 1},
    'round_of_16': {'name': '1/8决赛', 'name_cn': '1/8决赛（16强）', 'rounds': 1},
    'quarter_final': {'name': '1/4决赛', 'name_cn': '1/4决赛（8强）', 'rounds': 1},
    'semi_final': {'name': '半决赛', 'name_cn': '半决赛', 'rounds': 1},
    'third_place': {'name': '三四名决赛', 'name_cn': '季军争夺战', 'rounds': 1},
    'final': {'name': '决赛', 'name_cn': '决赛', 'rounds': 1}
}

with open('data/schedule_2026.json', 'w', encoding='utf-8') as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)

group_count = sum(1 for m in schedule['matches'] if m['stage'] == 'group')
ko_count = sum(1 for m in schedule['matches'] if m['stage'] != 'group')
print(f'Created schedule with {len(schedule["matches"])} matches ({group_count} group + {ko_count} knockout)')
