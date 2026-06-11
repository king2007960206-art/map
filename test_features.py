import unittest
import sys
import os
import json

# Add root folder to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.db import get_db_connection
from app.models.user import UserProfile
from app.models.report import Report

class TestMutualAidCommunity(unittest.TestCase):
    def setUp(self):
        # Set up Flask test client
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear database and initialize it fresh
        self.conn = get_db_connection()
        self.conn.execute('DELETE FROM user_profiles')
        self.conn.execute('DELETE FROM reports')
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_full_community_flow(self):
        print("\n=== 開始進行『用戶貢獻與互助社群』自動化集成測試 ===")
        
        # 1. 測試使用者訪問首頁自動初始化 Profile
        user_session = "test-session-12345"
        with self.client.session_transaction() as sess:
            sess['user_session'] = user_session
            
        print("步驟 1: 模擬首頁訪問，驗證會話與個人檔案初始化...")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        profile = UserProfile.get_or_create(user_session)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['nickname'], "匿名守護者-2345")
        self.assertEqual(profile['points'], 0)
        self.assertEqual(profile['level_name'], "校園初學者")
        self.assertEqual(profile['reports_count'], 0)
        print(f"   [成功] 用戶自動建立，暱稱: {profile['nickname']}, 積分: {profile['points']}")

        # 2. 測試自訂暱稱功能
        print("步驟 2: 測試更換暱稱 API (POST /api/user/nickname)...")
        new_nickname = "逢甲小幫手"
        response = self.client.post('/api/user/nickname', 
                                    data=json.dumps({"nickname": new_nickname}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data['profile']['nickname'], new_nickname)
        
        # 再次查詢確認寫入資料庫
        profile = UserProfile.get_or_create(user_session)
        self.assertEqual(profile['nickname'], new_nickname)
        print(f"   [成功] 暱稱成功更新為: {profile['nickname']}")

        # 3. 測試回報功能與積分累計
        print("步驟 3: 測試提交回報 API，驗證獲得 10 積分 (POST /api/report)...")
        report_data = {
            "location_id": 1, # 圖書館
            "crowd_level": "medium",
            "temperature_felt": "comfort"
        }
        response = self.client.post('/api/report',
                                    data=json.dumps(report_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        
        # 驗證回報成功回傳的 Profile 點數是否為 10
        self.assertEqual(res_data['profile']['points'], 10)
        self.assertEqual(res_data['profile']['reports_count'], 1)
        
        # 查詢資料庫確認點數與回報次數
        profile = UserProfile.get_or_create(user_session)
        self.assertEqual(profile['points'], 10)
        self.assertEqual(profile['reports_count'], 1)
        print(f"   [成功] 回報完成，用戶目前積分: {profile['points']}, 回報次數: {profile['reports_count']}")

        # 4. 測試等級晉升機制
        print("步驟 4: 測試大量回報後的等級晉升 (校園探索者 50分)...")
        # 模擬加分到 50 分
        updated_profile = UserProfile.add_points(user_session, amount=40, is_report=False)
        self.assertEqual(updated_profile['points'], 50)
        self.assertEqual(updated_profile['level_name'], "校園探索者")
        print(f"   [成功] 積分達 {updated_profile['points']}，等級晉升為: {updated_profile['level_name']}")

        # 5. 測試管理員異常標記與扣分處罰
        print("步驟 5: 測試管理員標記回報為異常 (POST /api/admin/reports/<id>/abnormal)...")
        # 取得剛才建立的回報
        reports = Report.get_all_recent(limit=1)
        self.assertEqual(len(reports), 1)
        report_id = reports[0]['id']
        
        # 呼叫標記異常 API
        response = self.client.post(f'/api/admin/reports/{report_id}/abnormal')
        self.assertEqual(response.status_code, 200)
        
        # 驗證積分扣除 20 分（50 - 20 = 30分），且等級稱號重新計算
        profile = UserProfile.get_or_create(user_session)
        self.assertEqual(profile['points'], 30)
        self.assertEqual(profile['level_name'], "校園初學者")
        
        # 驗證該筆回報已被標記為異常 (is_abnormal = 1)
        db_report = self.conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        self.assertEqual(db_report['is_abnormal'], 1)
        print(f"   [成功] 回報被標記為異常！用戶積分扣至: {profile['points']} 分，稱號降回: {profile['level_name']}")

        # 6. 測試異常恢復與分數補回
        print("步驟 6: 測試管理員還原異常為正常 (POST /api/admin/reports/<id>/normal)...")
        response = self.client.post(f'/api/admin/reports/{report_id}/normal')
        self.assertEqual(response.status_code, 200)
        
        # 驗證積分加回 20 分 (30 + 20 = 50分)，且等級稱號重新計算
        profile = UserProfile.get_or_create(user_session)
        self.assertEqual(profile['points'], 50)
        self.assertEqual(profile['level_name'], "校園探索者")
        
        # 驗證該筆回報已還原為正常 (is_abnormal = 0)
        db_report = self.conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        self.assertEqual(db_report['is_abnormal'], 0)
        print(f"   [成功] 回報恢復正常！用戶積分還原為: {profile['points']} 分，稱號恢復為: {profile['level_name']}")
        print("=== 所有『用戶貢獻與互助社群』自動化測試項目全部通過 ===\n")

if __name__ == '__main__':
    unittest.main()
