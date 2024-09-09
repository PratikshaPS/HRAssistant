css = '''
<style>
.chat-message {
    padding: 10px; 
    border-radius: 0.5rem; 
    margin-bottom: 0.5rem; 
    display: flex
}
.chat-message.user {
    background-color: #262730
}
.chat-message.bot {
    background-color: transparent
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 40px;
  max-height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 5px;
  color: #fff;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://tl.vhv.rs/dpng/s/366-3661417_female-virtual-assistant-icon-hd-png-download.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://static.vecteezy.com/system/resources/previews/024/183/535/non_2x/male-avatar-portrait-of-a-young-man-with-glasses-illustration-of-male-character-in-modern-color-style-vector.jpg">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''