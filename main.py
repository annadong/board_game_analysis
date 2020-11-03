from boardgame_api import BGGAPI
from nlp_keyword import TextRank4Keyword
import sys, getopt

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    ORANGE = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m' 
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _format_output(text_list, indent_size=10):
    output = ''
    step_size = 5
    
    new_list = [t.ljust(10) if len(t) < indent_size else t for t in text_list]
    for i in range(0, len(new_list), step_size):
        output += '\t'.join(new_list[i:i + step_size]) + '\n\t   '

    return output

def run(board_game_name):
    api = BGGAPI()
    bg = api.fetch_boardgame(board_game_name)
    reviews =  api.fetch_reviews(bg.bgid, 5)
    reviews_txt = '. '.join(reviews)
    tr4w = TextRank4Keyword()
    tr4w.analyze(reviews_txt, candidate_pos = ['NOUN', 'PROPN'], window_size=10, lower=True)
    keywords = tr4w.get_keywords(20)
    keywords_str = _format_output(keywords)

    normal_comments_text = '. '.join(bg.normal_comments)
    okay_comments_text = '. '.join(bg.okay_comments)
    bad_comments_text = '. '.join(bg.bad_comments)
    good_comments_text = '. '.join(bg.good_comments)

    tr_normal = TextRank4Keyword()
    tr_normal.analyze(normal_comments_text, candidate_pos = ['NOUN', 'PROPN'], window_size=10, lower=True)
    tr_okay = TextRank4Keyword()
    tr_okay.analyze(okay_comments_text, candidate_pos = ['NOUN', 'PROPN'], window_size=10, lower=True)
    tr_bad = TextRank4Keyword()
    tr_bad.analyze(bad_comments_text, candidate_pos = ['NOUN', 'PROPN'], window_size=10, lower=True)
    tr_good = TextRank4Keyword()
    tr_good.analyze(good_comments_text, candidate_pos = ['NOUN', 'PROPN'], window_size=10, lower=True)

    normal_keywords = tr_normal.get_keywords(10)
    normal_keywords_str = _format_output(normal_keywords)

    okay_keywords = tr_okay.get_keywords(10)
    okay_keywords_str = _format_output(okay_keywords)

    bad_keywords = tr_bad.get_keywords(10)
    bad_keywords_str = _format_output(bad_keywords)

    good_keywords = tr_good.get_keywords(10)
    good_keywords_str = _format_output(good_keywords)

    mechanics_str = ', '.join(bg.mechanics)
    categories_str= ', '.join(bg.categories)

    print(
        '''
        ================================================================================================
        SUMMARY FOR {header_color}{game_name}{color_end}
        ================================================================================================
        
        {bold}minplayers{color_end}: {minplayers}   {bold}maxplayers{color_end}: {maxplayers}   {bold}playing time{color_end}: {time} min

        {bold}categories{color_end}: 
        {categories}
        
        {bold}mechanics{color_end}: 
        {mechanics}

        {good_color}{bold}keywords from reviews with good rating (> 6.5): 
        {good_keywords}{color_end}

        {bad_color}{bold}keywords for reviews with bad rating (< 3.5): 
        {bad_keywords}{color_end}

        {okay_color}{bold}keywords for reviews with okay rating (3.5 < rating < 6.5): 
        {okay_keywords}{color_end}

        keywords for reviews with no rating: 
        {normal_keywords}

        general keywords from reviews:
        {keywords}

        '''.format(
            game_name=board_game_name.upper(),
            minplayers=bg.minplayers,
            maxplayers=bg.maxplayers,
            categories='   ' + categories_str,
            mechanics='   ' + mechanics_str,
            keywords='   ' + keywords_str,
            header_color=bcolors.OKBLUE,
            color_end=bcolors.ENDC,
            bold=bcolors.BOLD,
            time=bg.playingtime,
            normal_keywords='   ' + normal_keywords_str,
            good_keywords='   ' + good_keywords_str,
            okay_keywords='   ' + okay_keywords_str,
            bad_keywords='   ' + bad_keywords_str,
            good_color=bcolors.OKGREEN,
            bad_color=bcolors.FAIL,
            okay_color=bcolors.ORANGE
        )
    )

if __name__ == "__main__":
    if len(sys.argv) == 2:
        run(sys.argv[1])
    else:
        print('yo, you forgot to write a board game, or put quotes around the name if there white space')