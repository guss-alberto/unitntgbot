use dotenv::dotenv;
use teloxide::dispatching::dialogue::GetChatId;
use teloxide::prelude::*;
use teloxide::types::{InlineKeyboardButton, InlineKeyboardMarkup};
use teloxide::utils::command::BotCommands;

#[derive(BotCommands, Clone, Debug)]
#[command(
    rename_rule = "lowercase",
    description = "These commands are supported:"
)]
enum Command {
    #[command(description = "display this text.")]
    Help,
    #[command(description = "handle a username.")]
    Username(String),
    #[command(description = "handle a username and an age.", parse_with = "split")]
    UsernameAndAge { username: String, age: u8 },
}

// This is just a test to see how the bot works in Rust it's not the backend of the project
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenv().unwrap();

    pretty_env_logger::init();
    log::info!("Starting command bot...");
    
    // let handler = dptree::entry();

    let bot = Bot::from_env();

    // teloxide::repl(bot, |bot: Bot, msg: Message| async move {
    //     bot.send_message(msg.chat.id,"TEST1").await?;
    //     Ok(())
    // })
    // .await;

    Command::repl(bot, answer).await;

    Ok(())
}

fn make_keyboard() -> InlineKeyboardMarkup {
  let mut keyboard: Vec<Vec<InlineKeyboardButton>> = vec![];

  let debian_versions = [
      "Buzz", "Rex", "Bo", "Hamm", "Slink", "Potato", "Woody", "Sarge", "Etch", "Lenny",
      "Squeeze", "Wheezy", "Jessie", "Stretch", "Buster", "Bullseye",
  ];

  for versions in debian_versions.chunks(3) {
      let row = versions
          .iter()
          .map(|&version| InlineKeyboardButton::callback(version.to_owned(), version.to_owned()))
          .collect();

      keyboard.push(row);
  }

  InlineKeyboardMarkup::new(keyboard)
}

async fn answer(bot: Bot, msg: Message, cmd: Command) -> ResponseResult<()> {
    match cmd {
        Command::Help => {
            bot.send_message(msg.chat.id, Command::descriptions().to_string())
                .await?
        }
        Command::Username(username) => {
            bot.send_message(msg.chat.id, format!("Your username is @{username}."))
                .await?
        }
        Command::UsernameAndAge { username, age } => {
            let reply_markup = make_keyboard();

            bot.send_message(msg.chat.id, "test").reply_markup(reply_markup).await?
            // bot.send_message(
            //     msg.chat.id,
            //     format!("Your username is @{username} and age is {age}."),
            // )
            // .await?
        }
    };

    Ok(())
}
