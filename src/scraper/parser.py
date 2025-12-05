"""
HTMLパーサーモジュール
netkeiba.comのHTMLからデータを抽出
"""

from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import re
from datetime import datetime


class NetkeibaParser:
    """netkeiba.com用HTMLパーサー"""

    @staticmethod
    def parse_race_info(html: str, race_id: str) -> Optional[Dict[str, Any]]:
        """
        レース情報をパース（新しいHTML構造に対応）

        Args:
            html: レースページのHTML
            race_id: レースID

        Returns:
            レース情報の辞書
        """
        soup = BeautifulSoup(html, 'lxml')

        try:
            # レース名を取得（race_head > h1）
            race_head = soup.find('div', class_='race_head')
            race_name = ""
            if race_head:
                h1 = race_head.find('h1')
                if h1:
                    race_name = h1.text.strip()

            if not race_name:
                return None

            # レース詳細情報を取得（data_intro または mainrace_data）
            data_intro = soup.find('div', class_='data_intro')
            if not data_intro:
                data_intro = soup.find('div', class_='mainrace_data')

            if not data_intro:
                return None

            race_data_text = data_intro.text.strip()

            # 距離と馬場種別を抽出（芝、ダート、障害）
            # 例: "ダ右1200m" または "芝1600m"
            distance_match = re.search(r'(芝|ダ|ダート|障害)[^0-9]*(\d+)m', race_data_text)
            track_type = ""
            distance = 0
            if distance_match:
                track_type_raw = distance_match.group(1)
                # "ダ" を "ダート" に正規化
                if track_type_raw == "ダ":
                    track_type = "ダート"
                else:
                    track_type = track_type_raw
                distance = int(distance_match.group(2))

            # 馬場状態（芝の場合は "芝 : 良"、ダートの場合は "ダート : 良"）
            track_condition = ""
            if track_type == "芝":
                condition_match = re.search(r'芝\s*[:：]\s*(良|稍重|重|不良)', race_data_text)
                if condition_match:
                    track_condition = condition_match.group(1)
            elif track_type == "ダート":
                condition_match = re.search(r'ダート\s*[:：]\s*(良|稍重|重|不良)', race_data_text)
                if condition_match:
                    track_condition = condition_match.group(1)

            # 天気
            weather = ""
            weather_match = re.search(r'天候\s*[:：]\s*(晴|曇|雨|雪|小雨|小雪)', race_data_text)
            if weather_match:
                weather = weather_match.group(1)

            # 日付と競馬場を抽出
            # 例: "2020年01月05日 1回中山1日目"
            date_str = ""
            venue = ""
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', race_data_text)
            if date_match:
                year, month, day = date_match.groups()
                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            venue_match = re.search(r'(札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)', race_data_text)
            if venue_match:
                venue = venue_match.group(1)

            # レースクラス
            race_class = ""
            grade = ""
            if 'G1' in race_name or 'ＧⅠ' in race_name or 'GⅠ' in race_name:
                grade = "G1"
            elif 'G2' in race_name or 'ＧⅡ' in race_name or 'GⅡ' in race_name:
                grade = "G2"
            elif 'G3' in race_name or 'ＧⅢ' in race_name or 'GⅢ' in race_name:
                grade = "G3"
            elif 'オープン' in race_name or 'OP' in race_name or 'オープン' in race_data_text:
                race_class = "オープン"
            elif '3勝' in race_name or '3勝' in race_data_text:
                race_class = "3勝クラス"
            elif '2勝' in race_name or '2勝' in race_data_text:
                race_class = "2勝クラス"
            elif '1勝' in race_name or '1勝' in race_data_text:
                race_class = "1勝クラス"
            elif '未勝利' in race_name or '未勝利' in race_data_text:
                race_class = "未勝利"
            elif '新馬' in race_name or '新馬' in race_data_text:
                race_class = "新馬"

            # レース番号をrace_idの最後2桁から抽出
            # 例: 201506010102 → 02 → レース番号2
            race_number = None
            if race_id and len(race_id) >= 2:
                try:
                    race_number = int(race_id[-2:])
                except ValueError:
                    pass

            return {
                'race_id': race_id,
                'race_name': race_name,
                'date': date_str,
                'venue': venue,
                'distance': distance,
                'track_type': track_type,
                'track_condition': track_condition,
                'weather': weather,
                'race_class': race_class,
                'grade': grade,
                'race_number': race_number
            }

        except Exception as e:
            print(f"レース情報パースエラー: {e}")
            return None

    @staticmethod
    def parse_race_results(html: str, race_id: str) -> List[Dict[str, Any]]:
        """
        レース結果をパース

        Args:
            html: レースページのHTML
            race_id: レースID

        Returns:
            レース結果のリスト
        """
        soup = BeautifulSoup(html, 'lxml')
        results = []

        try:
            # 結果テーブルを取得（新しいHTML構造: race_table_01）
            result_table = soup.find('table', class_='race_table_01')

            if not result_table:
                return results

            rows = result_table.find_all('tr')

            for row in rows[1:]:  # ヘッダー行をスキップ
                cols = row.find_all('td')
                if len(cols) < 10:
                    continue

                # 着順
                finishing_position_text = cols[0].text.strip()
                try:
                    finishing_position = int(re.search(r'\d+', finishing_position_text).group())
                except:
                    finishing_position = None

                # 枠番
                bracket_number_text = cols[1].text.strip()
                bracket_number = int(bracket_number_text) if bracket_number_text.isdigit() else None

                # 馬番
                horse_number_text = cols[2].text.strip()
                horse_number = int(horse_number_text) if horse_number_text.isdigit() else None

                # 馬名とID
                horse_link = cols[3].find('a')
                horse_name = horse_link.text.strip() if horse_link else cols[3].text.strip()
                horse_id = ""
                if horse_link and 'href' in horse_link.attrs:
                    horse_id_match = re.search(r'/horse/([^/]+)', horse_link['href'])
                    if horse_id_match:
                        horse_id = horse_id_match.group(1)

                # 性齢
                sex_age = cols[4].text.strip()
                sex = sex_age[0] if sex_age else ""
                age = sex_age[1:] if len(sex_age) > 1 else ""

                # 斤量
                jockey_weight_text = cols[5].text.strip()
                try:
                    jockey_weight = float(jockey_weight_text)
                except:
                    jockey_weight = None

                # 騎手
                jockey_link = cols[6].find('a')
                jockey_name = jockey_link.text.strip() if jockey_link else cols[6].text.strip()
                jockey_id = ""
                if jockey_link and 'href' in jockey_link.attrs:
                    jockey_id_match = re.search(r'/jockey/([^/]+)', jockey_link['href'])
                    if jockey_id_match:
                        jockey_id = jockey_id_match.group(1)

                # タイム
                time_text = cols[7].text.strip()
                time_seconds = None
                if ':' in time_text:
                    time_parts = time_text.split(':')
                    if len(time_parts) == 2:
                        try:
                            minutes = int(time_parts[0])
                            seconds = float(time_parts[1])
                            time_seconds = minutes * 60 + seconds
                        except:
                            pass

                # 着差
                margin = cols[8].text.strip()

                # タイム指数（プレミアム情報）
                time_index = None
                if len(cols) > 9:
                    time_index_text = cols[9].text.strip()
                    if time_index_text and time_index_text.isdigit():
                        time_index = int(time_index_text)

                # 通過順位
                passing_order = cols[10].text.strip() if len(cols) > 10 else ""

                # 上がり3ハロン（秒）
                last_3f_text = cols[11].text.strip() if len(cols) > 11 else ""
                last_3f = None
                if last_3f_text:
                    try:
                        last_3f = float(last_3f_text)
                    except:
                        pass

                # 人気
                popularity_text = cols[13].text.strip() if len(cols) > 13 else ""
                try:
                    popularity = int(popularity_text)
                except:
                    popularity = None

                # 単勝オッズ
                odds_text = cols[12].text.strip() if len(cols) > 12 else ""
                try:
                    odds_win = float(odds_text)
                except:
                    odds_win = None

                # 複勝オッズ（範囲の場合は平均値を使用）
                odds_place = None
                if len(cols) > 13:
                    odds_place_text = cols[13].text.strip()
                    if odds_place_text and odds_place_text != '---':
                        try:
                            # "2.1-3.4" のような範囲の場合
                            if '-' in odds_place_text:
                                parts = odds_place_text.split('-')
                                odds_place = (float(parts[0]) + float(parts[1])) / 2
                            else:
                                odds_place = float(odds_place_text)
                        except:
                            pass

                # 馬体重
                weight_text = cols[14].text.strip() if len(cols) > 14 else ""
                horse_weight = None
                horse_weight_diff = None
                if weight_text:
                    weight_match = re.match(r'(\d+)\(([+\-]?\d+)\)', weight_text)
                    if weight_match:
                        horse_weight = int(weight_match.group(1))
                        horse_weight_diff = int(weight_match.group(2))

                # 備考（プレミアム情報）
                remarks = ""
                if len(cols) > 17:
                    remarks = cols[17].text.strip()

                # 調教師
                trainer_name = ""
                trainer_id = ""
                if len(cols) > 18:
                    trainer_link = cols[18].find('a')
                    if trainer_link:
                        trainer_name = trainer_link.text.strip()
                        if 'href' in trainer_link.attrs:
                            trainer_id_match = re.search(r'/trainer/([^/]+)', trainer_link['href'])
                            if trainer_id_match:
                                trainer_id = trainer_id_match.group(1)

                result = {
                    'race_id': race_id,
                    'horse_id': horse_id,
                    'horse_name': horse_name,
                    'finishing_position': finishing_position,
                    'bracket_number': bracket_number,
                    'horse_number': horse_number,
                    'jockey_id': jockey_id,
                    'jockey_name': jockey_name,
                    'jockey_weight': jockey_weight,
                    'trainer_id': trainer_id,
                    'trainer_name': trainer_name,
                    'horse_weight': horse_weight,
                    'horse_weight_diff': horse_weight_diff,
                    'odds_win': odds_win,
                    'odds_place': odds_place,
                    'popularity': popularity,
                    'time': time_seconds,
                    'margin': margin,
                    'passing_order': passing_order,
                    'last_3f': last_3f,
                    'sex': sex,
                    'age': age,
                    # プレミアム情報
                    'time_index': time_index,
                    'remarks': remarks
                }

                results.append(result)

        except Exception as e:
            print(f"レース結果パースエラー: {e}")

        return results

    @staticmethod
    def parse_payouts(html: str, race_id: str) -> List[Dict[str, Any]]:
        """
        払戻金情報をパース

        Args:
            html: レースページのHTML
            race_id: レースID

        Returns:
            払戻金情報のリスト
        """
        soup = BeautifulSoup(html, 'lxml')
        payouts = []

        try:
            # 払戻金テーブルを全て取得（左右2つのテーブルに分かれている）
            payout_tables = soup.find_all('table', class_='pay_table_01')
            if not payout_tables:
                return payouts

            # 全てのテーブルを処理
            for payout_table in payout_tables:
                rows = payout_table.find_all('tr')

                for row in rows:
                    # 払戻タイプ（単勝、複勝など）
                    th = row.find('th')
                    if not th:
                        continue

                    payout_type = th.text.strip()

                    # データベースのCHECK制約に合わせて正規化
                    payout_type = payout_type.replace('三連複', '3連複').replace('三連単', '3連単')

                    print(f"DEBUG: Found payout_type: '{payout_type}' for race {race_id}")

                    # 払戻データ
                    tds = row.find_all('td')
                    if len(tds) < 2:
                        continue

                    # 組み合わせ（馬番）- 複数ある場合は<br>で区切られている
                    combination_td = tds[0]
                    # <br>タグで分割して複数の組み合わせを取得
                    combinations = []
                    if combination_td.find('br'):
                        # <br>で区切られている場合
                        for text in combination_td.stripped_strings:
                            if text.strip():
                                combinations.append(text.strip())
                    else:
                        # 単一の組み合わせ
                        combinations.append(combination_td.text.strip())

                    # 払戻金額 - 複数ある場合は<br>で区切られている
                    payout_td = tds[1]
                    payout_amounts = []
                    if payout_td.find('br'):
                        # <br>で区切られている場合
                        for text in payout_td.stripped_strings:
                            text = text.strip().replace(',', '').replace('円', '')
                            if text:
                                try:
                                    payout_amounts.append(int(text))
                                except:
                                    print(f"DEBUG: Failed to parse payout amount: '{text}'")
                    else:
                        # 単一の払戻金
                        payout_text = payout_td.text.strip().replace(',', '').replace('円', '')
                        try:
                            payout_amounts.append(int(payout_text))
                        except:
                            print(f"DEBUG: Failed to parse payout amount: '{payout_text}'")
                            continue

                    # 人気 - 複数ある場合は<br>で区切られている
                    popularities = []
                    if len(tds) > 2:
                        popularity_td = tds[2]
                        if popularity_td.find('br'):
                            # <br>で区切られている場合
                            for text in popularity_td.stripped_strings:
                                text = text.strip().replace('番人気', '')
                                if text:
                                    try:
                                        popularities.append(int(text))
                                    except:
                                        pass
                        else:
                            # 単一の人気
                            popularity_text = popularity_td.text.strip().replace('番人気', '')
                            try:
                                popularities.append(int(popularity_text))
                            except:
                                pass

                    # 組み合わせと払戻金額が同じ数だけあることを確認
                    if len(combinations) != len(payout_amounts):
                        print(f"WARNING: Combination count ({len(combinations)}) != payout count ({len(payout_amounts)}) for {payout_type}")
                        print(f"  Combinations: {combinations}")
                        print(f"  Payouts: {payout_amounts}")
                        # 数が合わない場合はスキップ
                        continue

                    # 人気の数を調整（人気が1つだけの場合は全ての組み合わせで共有）
                    if len(popularities) == 1:
                        popularities = popularities * len(combinations)
                    elif len(popularities) != len(combinations):
                        # 人気の数が合わない場合はNoneで埋める
                        popularities = [None] * len(combinations)

                    # 各組み合わせと払戻金のペアを個別のエントリとして追加
                    for combination, payout_amount, popularity in zip(combinations, payout_amounts, popularities):
                        print(f"DEBUG: Parsed payout - type: '{payout_type}', combination: '{combination}', amount: {payout_amount}, popularity: {popularity}")
                        payouts.append({
                            'race_id': race_id,
                            'payout_type': payout_type,
                            'combination': combination,
                            'payout': payout_amount,
                            'popularity': popularity
                        })

        except Exception as e:
            print(f"払戻金パースエラー: {e}")

        return payouts

    @staticmethod
    def parse_odds(html: str, race_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        オッズ情報をパース

        Args:
            html: オッズページのHTML
            race_id: レースID

        Returns:
            オッズ情報の辞書
        """
        # TODO: オッズページのパース実装
        # 現時点では基本実装のみ
        return {}

    @staticmethod
    def parse_horse_pedigree(html: str, horse_id: str) -> Dict[str, Any]:
        """
        馬の血統情報をパース（血統詳細ページから）

        血統詳細ページ (/horse/ped/{horse_id}/) の5代血統表から取得
        ※馬詳細ページの血統情報は動的ロードのため使用不可

        Args:
            html: 血統詳細ページのHTML
            horse_id: 馬ID

        Returns:
            血統情報の辞書（sire, dam, damsire, sire_sire, sire_dam, dam_dam）
        """
        soup = BeautifulSoup(html, 'lxml')
        pedigree = {}

        try:
            # 5代血統表を取得
            # <table summary="5代血統表" class="blood_table detail">
            blood_table = soup.find('table', summary=lambda x: x and '血統表' in x)

            if not blood_table:
                # fallback: class指定で探す
                blood_table = soup.find('table', class_='blood_table')

            if blood_table:
                # 全てのtdセルを取得
                cells = blood_table.find_all('td')

                # rowspan="16" のセルを探す（父と母）
                rowspan_16_cells = [cell for cell in cells if cell.get('rowspan') == '16']

                # 父: 最初の rowspan="16" かつ class="b_ml"
                for cell in rowspan_16_cells:
                    if 'b_ml' in cell.get('class', []):
                        link = cell.find('a')
                        if link:
                            pedigree['sire'] = link.text.strip()
                        break

                # 母: 最初の rowspan="16" かつ class="b_fml"
                for cell in rowspan_16_cells:
                    if 'b_fml' in cell.get('class', []):
                        link = cell.find('a')
                        if link:
                            pedigree['dam'] = link.text.strip()
                        break

                # rowspan="8" のセルを探す（祖父母）
                # 順番：父父(b_ml), 父母(b_fml), 母父(b_ml), 母母(b_fml)
                rowspan_8_cells = [cell for cell in cells if cell.get('rowspan') == '8']

                # b_ml (male line) と b_fml (female line) で分類
                ml_cells = [cell for cell in rowspan_8_cells if 'b_ml' in cell.get('class', [])]
                fml_cells = [cell for cell in rowspan_8_cells if 'b_fml' in cell.get('class', [])]

                # 父父: 最初の b_ml
                if len(ml_cells) >= 1:
                    link = ml_cells[0].find('a')
                    if link:
                        # 改行で分割して最初の行（馬名）のみを取得
                        pedigree['sire_sire'] = link.text.strip().split('\n')[0].strip()

                # 父母: 最初の b_fml
                if len(fml_cells) >= 1:
                    link = fml_cells[0].find('a')
                    if link:
                        # 改行で分割して最初の行（馬名）のみを取得
                        pedigree['sire_dam'] = link.text.strip().split('\n')[0].strip()

                # 母父: 2番目の b_ml
                if len(ml_cells) >= 2:
                    link = ml_cells[1].find('a')
                    if link:
                        # 改行で分割して最初の行（馬名）のみを取得
                        pedigree['damsire'] = link.text.strip().split('\n')[0].strip()

                # 母母: 2番目の b_fml
                if len(fml_cells) >= 2:
                    link = fml_cells[1].find('a')
                    if link:
                        # 改行で分割して最初の行（馬名）のみを取得
                        pedigree['dam_dam'] = link.text.strip().split('\n')[0].strip()

        except Exception as e:
            print(f"血統情報パースエラー: {e}")
            import traceback
            traceback.print_exc()

        return pedigree

    @staticmethod
    def parse_race_list(html: str) -> List[str]:
        """
        日付別レースリストページからレースIDを抽出（JRA中央競馬のみ）

        Args:
            html: レースリストページのHTML

        Returns:
            レースIDのリスト（JRA中央競馬のみ：競馬場コード01-10）
        """
        soup = BeautifulSoup(html, 'lxml')
        race_ids = []

        try:
            # レースへのリンクを全て取得
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                href = link.get('href', '')
                # レースIDを抽出（12桁の数字）
                match = re.search(r'/race/(\d{12})/?', href)
                if match:
                    race_id = match.group(1)

                    # JRA中央競馬のみフィルタリング（競馬場コード01-10）
                    # フォーマット: 年(4) + 競馬場(2) + 回次(2) + 日次(2) + レース番号(2)
                    venue_code = race_id[4:6]  # 5-6桁目が競馬場コード

                    if venue_code.isdigit() and 1 <= int(venue_code) <= 10:
                        if race_id not in race_ids:  # 重複排除
                            race_ids.append(race_id)

        except Exception as e:
            print(f"レースリストパースエラー: {e}")
            import traceback
            traceback.print_exc()

        return race_ids

    @staticmethod
    def parse_premium_race_info(html: str, race_id: str) -> Optional[Dict[str, Any]]:
        """
        レース詳細ページからプレミアム情報をパース

        Args:
            html: レースページのHTML
            race_id: レースID

        Returns:
            プレミアム情報の辞書（馬場指数、馬場コメント、レース分析、注目馬短評）
        """
        soup = BeautifulSoup(html, 'lxml')
        premium_info = {
            'race_id': race_id,
            'track_index': None,
            'track_comment': None,
            'race_analysis_comment': None,
            'horse_short_reviews': []
        }

        try:
            # 馬場情報テーブルから馬場指数と馬場コメントを取得
            track_info_tables = soup.find_all('table', class_='result_table_02', summary='馬場情報')
            for table in track_info_tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        th_text = th.text.strip()
                        if '馬場指数' in th_text:
                            # "−3" のような形式
                            index_text = td.text.strip().split()[0]  # "?(...)"部分を除去
                            try:
                                premium_info['track_index'] = int(index_text.replace('−', '-'))
                            except:
                                pass
                        elif '馬場コメント' in th_text:
                            premium_info['track_comment'] = td.text.strip()

            # レース分析テーブルからコメントを取得
            analysis_tables = soup.find_all('table', class_='result_table_02', summary='レース分析')
            for table in analysis_tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td and '分析コメント' in th.text:
                        premium_info['race_analysis_comment'] = td.text.strip()
                        break

            # 注目馬短評テーブルから各馬の短評を取得
            review_tables = soup.find_all('table', class_='result_table_02', summary='注目馬 レース後の短評')
            for table in review_tables:
                rows = table.find_all('tr')
                current_horse = None
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')

                    if th:
                        # 馬名と着順を取得（例: "1着:オイデヤスダイジン"）
                        horse_info = th.text.strip()
                        # ヘッダー行や無効なデータをスキップ
                        if ':' not in horse_info:
                            continue
                        position_str, horse_name = horse_info.split(':', 1)
                        position_match = re.search(r'(\d+)着', position_str)
                        finishing_position = int(position_match.group(1)) if position_match else None
                        current_horse = {
                            'race_id': race_id,  # race_idを追加
                            'horse_id': None,  # horse_idは後でスクレイパーで設定
                            'horse_name': horse_name.strip(),
                            'finishing_position': finishing_position,
                            'review': None
                        }
                    elif td and current_horse:
                        # 短評を取得
                        current_horse['review'] = td.text.strip()
                        premium_info['horse_short_reviews'].append(current_horse)
                        current_horse = None

        except Exception as e:
            print(f"プレミアム情報パースエラー: {e}")
            import traceback
            traceback.print_exc()

        return premium_info

    @staticmethod
    def parse_training_times(html: str, horse_id: str, race_id: str) -> List[Dict[str, Any]]:
        """
        調教タイムページから調教情報をパース

        Args:
            html: 調教タイムページのHTML
            horse_id: 馬ID
            race_id: 対象レースID

        Returns:
            調教タイム情報のリスト
        """
        soup = BeautifulSoup(html, 'lxml')
        training_times = []

        try:
            # 調教タイムテーブルを取得
            training_tables = soup.find_all('table', class_='race_table_01')

            for table in training_tables:
                # レースIDが一致するテーブルのみ処理
                caption = table.find('caption')
                if not caption or race_id not in caption.text:
                    continue

                rows = table.find_all('tr')
                for row in rows[1:]:  # ヘッダー行をスキップ
                    cols = row.find_all('td')
                    if len(cols) < 8:
                        continue

                    # 日付
                    date_text = cols[0].text.strip()
                    date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_text)
                    training_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}" if date_match else None

                    # コース
                    course = cols[1].text.strip()

                    # 馬場状態
                    track_condition = cols[2].text.strip()

                    # 乗り役
                    rider = cols[3].text.strip()

                    # 調教タイム（TrainingTimeDataList内のli要素）
                    time_data = cols[4]
                    time_list = time_data.find_all('li')
                    time_6f = None
                    time_5f = None
                    time_4f = None
                    time_3f = None
                    time_1f = None

                    if len(time_list) >= 5:
                        try:
                            time_6f = float(time_list[0].text.strip()) if time_list[0].text.strip() != '-' else None
                        except:
                            pass
                        try:
                            time_5f = float(time_list[1].text.strip()) if time_list[1].text.strip() != '-' else None
                        except:
                            pass
                        try:
                            time_4f = float(time_list[2].text.strip()) if time_list[2].text.strip() != '-' else None
                        except:
                            pass
                        try:
                            time_3f = float(time_list[3].text.strip()) if time_list[3].text.strip() != '-' else None
                        except:
                            pass
                        try:
                            time_1f = float(time_list[4].text.strip()) if time_list[4].text.strip() != '-' else None
                        except:
                            pass

                    # 併せ馬情報（TrainingHeisou）
                    parallel_info_elem = time_data.find('p', class_='TrainingHeisou')
                    parallel_info = parallel_info_elem.text.strip() if parallel_info_elem else None

                    # 位置
                    position_text = cols[5].text.strip()
                    position = int(position_text) if position_text.isdigit() else None

                    # 脚色
                    intensity = cols[6].text.strip()

                    # 評価テキスト
                    evaluation_text = cols[7].text.strip()

                    # 評価グレード
                    evaluation_grade = cols[8].text.strip() if len(cols) > 8 else None

                    training_times.append({
                        'horse_id': horse_id,
                        'race_id': race_id,
                        'training_date': training_date,
                        'course': course,
                        'track_condition': track_condition,
                        'rider': rider,
                        'time_6f': time_6f,
                        'time_5f': time_5f,
                        'time_4f': time_4f,
                        'time_3f': time_3f,
                        'time_1f': time_1f,
                        'position': position,
                        'intensity': intensity,
                        'evaluation_text': evaluation_text,
                        'evaluation_grade': evaluation_grade,
                        'parallel_info': parallel_info
                    })

        except Exception as e:
            print(f"調教タイムパースエラー: {e}")
            import traceback
            traceback.print_exc()

        return training_times

    @staticmethod
    def parse_stable_comment(html: str, horse_id: str, race_id: str) -> Optional[str]:
        """
        厩舎コメントページからコメントをパース

        Args:
            html: 厩舎コメントページのHTML
            horse_id: 馬ID
            race_id: 対象レースID

        Returns:
            厩舎コメント（文字列）
        """
        soup = BeautifulSoup(html, 'lxml')

        try:
            # コメントテーブルを探す
            tables = soup.find_all('table', class_='border')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    td = row.find('td', class_='bml')
                    if td:
                        comment = td.text.strip()
                        return comment

        except Exception as e:
            print(f"厩舎コメントパースエラー: {e}")
            import traceback
            traceback.print_exc()

        return None

    @staticmethod
    def parse_lap_times(html: str, race_id: str) -> List[Dict[str, Any]]:
        """
        レース詳細ページからラップタイムをパース

        Args:
            html: レースページのHTML
            race_id: レースID

        Returns:
            ラップタイム情報のリスト（各区間ごとのデータ）
        """
        soup = BeautifulSoup(html, 'lxml')
        lap_times = []

        try:
            # ラップタイムテーブルを探す
            lap_table = soup.find('table', class_='result_table_02', summary='ラップタイム')
            if not lap_table:
                return lap_times

            rows = lap_table.find_all('tr')
            lap_row = None
            pace_row = None

            # 「ラップ」行と「ペース」行を探す
            for row in rows:
                th = row.find('th')
                if th:
                    if 'ラップ' in th.text:
                        lap_row = row
                    elif 'ペース' in th.text:
                        pace_row = row

            if not lap_row:
                return lap_times

            # ラップタイムのセルを取得
            td = lap_row.find('td', class_='race_lap_cell')
            if not td:
                return lap_times

            # ラップタイムを「-」で分割
            lap_text = td.text.strip()
            lap_values = [lap.strip() for lap in lap_text.split('-')]

            # ペース（累積時間）を取得
            pace_values = []
            if pace_row:
                pace_td = pace_row.find('td', class_='race_lap_cell')
                if pace_td:
                    pace_text = pace_td.text.strip()
                    pace_values = [pace.strip() for pace in pace_text.split('-')]

            # 各区間のラップタイムをデータベース用に変換
            # section: 1=0-200m, 2=200-400m, 3=400-600m...
            for section, lap_value in enumerate(lap_values, start=1):
                try:
                    lap_time_float = float(lap_value)

                    # ペース（累積時間）を取得
                    pace_float = None
                    if section <= len(pace_values):
                        try:
                            pace_float = float(pace_values[section - 1])
                        except ValueError:
                            pass

                    lap_times.append({
                        'race_id': race_id,
                        'section': section,
                        'lap_time': lap_time_float,
                        'pace': pace_float  # 累積時間
                    })
                except ValueError:
                    print(f"WARNING: Failed to parse lap time: '{lap_value}' for section {section}")
                    continue

        except Exception as e:
            print(f"ラップタイムパースエラー: {e}")
            import traceback
            traceback.print_exc()

        return lap_times
