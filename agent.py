import random
import pickle
import os
from collections import defaultdict

class QLearningRobot:
    """רובוט Q-Learning עם איפוס תגמול חכם + איפוס נקודות בטעינה - גרסה משופרת"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.3):
        # פרמטרי Q-Learning
        self.learning_rate = learning_rate      
        self.discount_factor = discount_factor  
        self.epsilon = epsilon                  
        
        # מצב הרובוט
        self.x = 19                             
        self.y = 9                             
        self.collision_count = 0               
        self.max_collisions = 5  # יותר סובלנות
        self.is_charging = False               
        self.charging_station = (1, 1)        
        
        # 🌟 החדש: מעקב אחר ניקוד אפיזוד נוכחי
        self.current_episode_reward = 0
        
        # פעולות אפשריות
        self.actions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.action_names = ['שמאל', 'ימין', 'למעלה', 'למטה']
        
        # Q-Table
        self.q_table = defaultdict(lambda: [0.0] * len(self.actions))
        
        # סטטיסטיקות
        self.episode_rewards = []              
        self.episode_steps = []                
        self.episode_collisions = []           
        self.success_episodes = []             
        
        print(f"🤖 רובוט משופר עם עונש קירות + איפוס רך נוצר!")
        print(f"📊 פרמטרים: LR={learning_rate}, γ={discount_factor}, ε={epsilon}")
        print(f"✨ חדש: עונש על התקרבות לקירות!")
        print(f"🔋 חדש: חזרה לטעינה = 0 (לא -200)!")
    
    def reset(self):
        """איפוס הרובוט למצב התחלתי"""
        self.x = 19
        self.y = 9
        self.collision_count = 0
        self.is_charging = False
        # 🌟 איפוס ניקוד אפיזוד
        self.current_episode_reward = 0
    
    def get_position(self):
        """החזרת מיקום הרובוט"""
        return (self.x, self.y)
    
    def get_wall_distance(self):
        """חישוב המרחק הקרוב ביותר לקיר"""
        distances = [
            self.x,           # מרחק לקיר שמאל
            19 - self.x,      # מרחק לקיר ימין
            self.y,           # מרחק לקיר עליון
            9 - self.y        # מרחק לקיר תחתון
        ]
        return min(distances)
    
    def encode_state(self, cats_positions, dirt_positions):
        """קידוד מצב מפורט יותר - מתמקד בחמקנות מחתולים + מרחק מקירות"""
        
        # מיקום הרובוט
        robot_zone_x = self.x // 5  # 4 אזורים אופקיים
        robot_zone_y = self.y // 3  # 3 אזורים אנכיים
        
        # 🆕 מרחק מקירות
        wall_distance = min(self.get_wall_distance(), 3)  # מקסימום 3 למטרת קידוד
        
        # ניתוח חתולים - היכן הם יחסית לרובוט?
        cat_threat_level = 0
        cat_direction = 4  # 0=שמאל, 1=ימין, 2=למעלה, 3=למטה, 4=רחוק
        
        if cats_positions:
            min_cat_distance = 999
            closest_cat = None
            
            for cat_pos in cats_positions:
                distance = abs(self.x - cat_pos[0]) + abs(self.y - cat_pos[1])
                if distance < min_cat_distance:
                    min_cat_distance = distance
                    closest_cat = cat_pos
            
            # רמת איום
            if min_cat_distance <= 1:
                cat_threat_level = 3  # סכנה מיידית!
            elif min_cat_distance <= 2:
                cat_threat_level = 2  # סכנה קרובה
            elif min_cat_distance <= 4:
                cat_threat_level = 1  # זהירות
            else:
                cat_threat_level = 0  # בטוח
            
            # כיוון החתול היחסי לרובוט
            if closest_cat and min_cat_distance <= 5:
                dx = closest_cat[0] - self.x
                dy = closest_cat[1] - self.y
                
                if abs(dx) > abs(dy):  # תנועה אופקית
                    cat_direction = 1 if dx > 0 else 0  # ימין או שמאל
                else:  # תנועה אנכית
                    cat_direction = 3 if dy > 0 else 2  # למטה או למעלה
        
        # ניתוח ליכלוכים
        dirt_count = len(dirt_positions)
        closest_dirt_distance = 999
        dirt_direction = 4  # כמו חתולים
        
        if dirt_positions:
            for dirt_pos in dirt_positions:
                distance = abs(self.x - dirt_pos[0]) + abs(self.y - dirt_pos[1])
                if distance < closest_dirt_distance:
                    closest_dirt_distance = distance
                    
                    # כיוון הליכלוך
                    dx = dirt_pos[0] - self.x
                    dy = dirt_pos[1] - self.y
                    
                    if abs(dx) > abs(dy):
                        dirt_direction = 1 if dx > 0 else 0
                    else:
                        dirt_direction = 3 if dy > 0 else 2
        
        # מצב מפורט יותר עם מרחק קירות
        state = (
            robot_zone_x,
            robot_zone_y,
            wall_distance,           # 🆕 מרחק מקירות
            cat_threat_level,        # רמת איום מחתולים
            cat_direction,           # כיוון החתול הקרוב
            min(dirt_count, 5),      # מספר ליכלוכים
            dirt_direction,          # כיוון הליכלוך הקרוב
            min(closest_dirt_distance, 10) // 2,  # מרחק לליכלוך
            min(self.collision_count, 5),  # מספר התנגשויות
            int(self.is_charging)
        )
        
        return state
    
    def choose_action(self, state):
        """בחירת פעולה עם עדיפות לחמקנות"""
        if random.random() < self.epsilon:
            return random.randint(0, len(self.actions) - 1)
        else:
            q_values = self.q_table[state]
            max_q = max(q_values)
            best_actions = [i for i, q in enumerate(q_values) if abs(q - max_q) < 0.001]
            return random.choice(best_actions)
    
    def is_valid_move(self, new_x, new_y):
        """בדיקה אם התנועה תקינה"""
        return 0 <= new_x < 20 and 0 <= new_y < 10
    
    def move(self, action):
        """ביצוע תנועה"""
        if self.is_charging:
            self.is_charging = False
            return True
            
        dx, dy = self.actions[action]
        new_x, new_y = self.x + dx, self.y + dy
        
        if self.is_valid_move(new_x, new_y):
            self.x, self.y = new_x, new_y
            return True
        else:
            return False
    
    def handle_collision(self):
        """טיפול בהתנגשות עם חתול"""
        self.collision_count += 1
        print(f"💥 התנגשות! סה\"כ: {self.collision_count}/{self.max_collisions}")
        
        if self.collision_count >= self.max_collisions:
            self.x, self.y = self.charging_station
            self.collision_count = 0
            self.is_charging = True
            
            # 🔋 החדש: איפוס נקודות כשחוזר לטעינה!
            old_score = self.current_episode_reward
            self.current_episode_reward = 0
            print(f"🔋 חזרה לעמדת טעינה! נקודות אופסו: {old_score:.0f} → 0 (ללא עונש!)")
            return True
        return False
    
    def calculate_reward(self, old_pos, cats_positions, dirt_positions, wall_hit, dirt_collected):
        """מערכת תגמולים משופרת עם עונש קירות וחזרה רכה לטעינה"""
        
        current_pos = (self.x, self.y)
        
        # 🌟 הרעיון החכם שלך: איפוס חכם על איסוף ליכלוך!
        if dirt_collected:
            if self.current_episode_reward < 0:
                # אם הניקוד שלילי - איפוס ל-0 ואז +200
                reset_amount = -self.current_episode_reward  # כמה צריך לאפס
                total_reward = reset_amount + 200
                print(f"🧹 ליכלוך נאסף! ניקוד היה {self.current_episode_reward:.0f} → איפוס + 200 = +{total_reward:.0f}")
                return total_reward
            else:
                # אם הניקוד חיובי - פשוט +200
                print(f"🧹 ליכלוך נאסף! ניקוד היה +{self.current_episode_reward:.0f} → +200 = +{self.current_episode_reward + 200:.0f}")
                return 200
        
        # אם לא תפס ליכלוך - מערכת עונשים רגילה
        reward = -0.05  # עונש קטן על כל צעד
        
        # עונש כבד על התנגשות
        collision_happened = current_pos in cats_positions
        if collision_happened:
            reward -= 100  # עונש כבד!
            print(f"💥 התנגשות! -100")
            went_to_charging = self.handle_collision()
            if went_to_charging:
                # 🆕 שינוי: לא -200, פשוט 0 (הנקודות כבר אופסו)
                print(f"🔋 חזרה לטעינה! (ללא עונש נוסף - נקודות אופסו)")
        
        # 🆕 עונש על התקרבות לקירות
        wall_distance = self.get_wall_distance()
        if wall_distance == 0:
            reward -= 25  # עונש בינוני על להיות צמוד לקיר
        elif wall_distance == 1:
            reward -= 10  # עונש קטן על להיות קרוב לקיר
        elif wall_distance == 2:
            reward -= 3   # עונש קטן מאוד על להיות די קרוב
        
        # תגמול על התרחקות מחתולים
        if cats_positions:
            current_min_cat_distance = min([abs(self.x - cat[0]) + abs(self.y - cat[1]) 
                                           for cat in cats_positions])
            old_min_cat_distance = min([abs(old_pos[0] - cat[0]) + abs(old_pos[1] - cat[1]) 
                                       for cat in cats_positions])
            
            # תגמול על התרחקות מחתולים
            if current_min_cat_distance > old_min_cat_distance:
                reward += 5  # תגמול על חמקנות
            elif current_min_cat_distance < old_min_cat_distance:
                reward -= 10  # עונש על התקרבות
            
            # עונש על להיות קרוב מדי
            if current_min_cat_distance <= 1:
                reward -= 30  # סכנה מיידית
            elif current_min_cat_distance == 2:
                reward -= 15  # סכנה קרובה
        
        # תגמול על התקרבות לליכלוך (רק אם לא מסוכן)
        if dirt_positions and not collision_happened:
            current_min_dirt_distance = min([abs(self.x - dirt[0]) + abs(self.y - dirt[1]) 
                                            for dirt in dirt_positions])
            old_min_dirt_distance = min([abs(old_pos[0] - dirt[0]) + abs(old_pos[1] - dirt[1]) 
                                       for dirt in dirt_positions])
            
            if current_min_dirt_distance < old_min_dirt_distance:
                reward += 3  # תגמול על התקרבות לליכלוך
        
        # עונש על פגיעה בקיר
        if wall_hit:
            reward -= 50  # עונש כבד כמו שרצית
        
        # בונוס על סיום משימה
        if len(dirt_positions) == 0:
            reward += 500  # בונוס נוסף
            print("🎉 משימה הושלמה! +500")
        
        return reward
    
    def update_q_table(self, state, action, reward, next_state, done):
        """עדכון Q-table"""
        current_q = self.q_table[state][action]
        
        if done:
            max_next_q = 0
        else:
            max_next_q = max(self.q_table[next_state])
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def step(self, cats_positions, dirt_positions):
        """צעד אחד של הרובוט"""
        current_state = self.encode_state(cats_positions, dirt_positions)
        old_pos = (self.x, self.y)
        
        action = self.choose_action(current_state)
        wall_hit = not self.move(action)
        
        current_pos = (self.x, self.y)
        dirt_collected = current_pos in dirt_positions
        
        reward = self.calculate_reward(old_pos, cats_positions, dirt_positions, wall_hit, dirt_collected)
        
        # 🌟 עדכון הניקוד המצטבר של האפיזוד (אלא אם כן אופס בטעינה)
        if not (self.x, self.y) == self.charging_station or not self.is_charging:
            self.current_episode_reward += reward
        
        done = len(dirt_positions) == 0
        
        if dirt_collected:
            new_dirt_positions = dirt_positions - {current_pos}
        else:
            new_dirt_positions = dirt_positions
            
        next_state = self.encode_state(cats_positions, new_dirt_positions)
        self.update_q_table(current_state, action, reward, next_state, done)
        
        return reward, done
    
    def decay_epsilon(self, decay_rate=0.995, min_epsilon=0.01):
        """הפחתת epsilon"""
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)
    
    def get_stats(self):
        """החזרת סטטיסטיקות"""
        if not self.episode_rewards:
            return {}
        
        def calculate_average(lst, last_n=100):
            if not lst:
                return 0
            recent = lst[-last_n:] if len(lst) > last_n else lst
            return sum(recent) / len(recent)
            
        return {
            'total_episodes': len(self.episode_rewards),
            'average_reward': calculate_average(self.episode_rewards, 100),
            'average_steps': calculate_average(self.episode_steps, 100),
            'success_rate': calculate_average(self.success_episodes, 100) if self.success_episodes else 0,
            'current_epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'current_episode_score': self.current_episode_reward,  # 🔋 נקודות נוכחיות
            'wall_distance': self.get_wall_distance()  # 🆕 מרחק נוכחי מקירות
        }
    
    def add_episode_stats(self, total_reward, steps, success):
        """הוספת סטטיסטיקות אפיזוד"""
        self.episode_rewards.append(total_reward)
        self.episode_steps.append(steps)
        self.success_episodes.append(1 if success else 0)
    
    def save_model(self, filename='improved_robot.pkl'):
        """שמירת מודל"""
        model_data = {
            'q_table': dict(self.q_table),
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_steps': self.episode_steps,
            'success_episodes': self.success_episodes
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"💾 רובוט משופר נשמר: {filename}")
    
    def load_model(self, filename='improved_robot.pkl'):
        """טעינת מודל"""
        if not os.path.exists(filename):
            print(f"❌ קובץ {filename} לא נמצא")
            return False
            
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = defaultdict(lambda: [0.0] * len(self.actions))
            self.q_table.update(model_data['q_table'])
            self.learning_rate = model_data.get('learning_rate', self.learning_rate)
            self.discount_factor = model_data.get('discount_factor', self.discount_factor)
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_steps = model_data.get('episode_steps', [])
            self.success_episodes = model_data.get('success_episodes', [])
            
            print(f"✅ רובוט משופר נטען: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ שגיאה: {e}")
            return False


# בדיקה מהירה
def test_improved_robot():
    """בדיקה של הרובוט המשופר"""
    print("🧪 בדיקת רובוט משופר עם עונש קירות...")
    
    robot = QLearningRobot(learning_rate=0.3, discount_factor=0.95, epsilon=0.5)
    
    # בדיקת מרחק מקירות
    print(f"📍 מיקום רובוט: {robot.get_position()}")
    print(f"🧱 מרחק מקירות: {robot.get_wall_distance()}")
    
    # סימולציית מצב
    cats_pos = [(18, 9)]  # חתול ליד הרובוט
    dirt_pos = {(15, 8)}  # ליכלוך רחוק
    
    print(f"🐱 מיקום חתול: {cats_pos}")
    print(f"🧹 מיקום ליכלוך: {dirt_pos}")
    print(f"💰 נקודות התחלתיות: {robot.current_episode_reward}")
    
    # סימולציית כמה צעדים
    for step in range(10):
        reward, done = robot.step(cats_pos, dirt_pos)
        robot_pos = robot.get_position()
        wall_dist = robot.get_wall_distance()
        
        print(f"צעד {step+1}: מיקום {robot_pos}, מרחק מקיר: {wall_dist}, תגמול: {reward:.2f}, נקודות: {robot.current_episode_reward:.2f}")
        
        if robot.is_charging:
            print("🔋 הרובוט בטעינה - הנקודות אופסו (ללא עונש נוסף)!")
            break
        
        if done:
            print("✅ משימה הושלמה!")
            break


if __name__ == "__main__":
    test_improved_robot()
